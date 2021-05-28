import argparse
import os
import sys
import time
import library.clients.entityclient as ec
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.status.tagstatus as tgkeys
import library.utils as utils

# Specify the source account and source user API key
# Also specify the target account and target user API key
# (if the same user has access to both accounts, this value may be the same)
# Specify the type of entity to search and migrate tags

logger = migrationlogger.get_logger(os.path.basename(__file__))
args = None


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate entity tags from one account to another')
    parser.add_argument('--fromFile', nargs=1, type=str, required=True, help='Path to file with entity names')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId local Store \
                                                                        like db/<sourceAccount>/monitors .')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account User API Key, \
                                                                                ignored if useLocal is passed')
    parser.add_argument('--targetAccount', nargs=1, type=str, required=True, help='Target accountId or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target account User API Key, \
                                                                        or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--synthetics', dest='synthetics', required=False, action='store_true',
                        help='Pass --synthetics to migrate Synthetic monitor entity tags')
    parser.add_argument('--securecreds', dest='securecreds', required=False, action='store_true',
                        help='Pass --securecreds to migrate Synthetic secure credentials entity tags')
    parser.add_argument('--apm', dest='apm', required=False, action='store_true',
                        help='Pass --apm to migrate APM entity tags')
    parser.add_argument('--browser', dest='browser', required=False, action='store_true',
                        help='Pass --browser to migrate Browser entity tags')
    parser.add_argument('--dashboards', dest='dashboards', required=False, action='store_true',
                        help='Pass --dashboards to migrate dashboard entity tags')
    parser.add_argument('--infrahost', dest='infrahost', required=False, action='store_true',
                        help='Pass --infrahost to migrate Infrastructure host entity tags')
    parser.add_argument('--infraint', dest='infraint', required=False, action='store_true',
                        help='Pass --infraint to migrate Infrastructure integration entity tags')
    parser.add_argument('--mobile', dest='mobile', required=False, action='store_true',
                        help='Pass --mobile to migrate Mobile entity tags')
    parser.add_argument('--lambda', dest='lambda_function', required=False, action='store_true',
                        help='Pass --lambda to migrate Lambda function entity tags')
    return parser


def parse_entity_types(args):
    entity_types = []
    if args.synthetics:
        entity_types.append(ec.SYNTH_MONITOR)
    if args.securecreds:
        entity_types.append(ec.SYNTH_SECURE_CRED)
    if args.apm:
        entity_types.append(ec.APM_APP)
    if args.browser:
        entity_types.append(ec.BROWSER_APP)
    if args.dashboards:
        entity_types.append(ec.DASHBOARD)
    if args.infrahost:
        entity_types.append(ec.INFRA_HOST)
    if args.infraint:
        entity_types.append(ec.INFRA_INT)
    if args.mobile:
        entity_types.append(ec.MOBILE_APP)
    if args.lambda_function:
        entity_types.append(ec.INFRA_LAMBDA)
    return entity_types


def migrate_tags(from_file: str, src_account_id: str, src_region: str, src_api_key: str,
                 tgt_account_id: str, tgt_region: str, tgt_api_key: str, entity_types):
    tag_status = {}
    entity_names = store.load_names(from_file)
    for entity_name in entity_names:
        tag_status[entity_name] = {}
        tag_status[entity_name][tgkeys.ENTITY_NAME] = entity_name
        logger.info('Migrating tags for entity ' + entity_name)
        src_entity = None
        for entity_type in entity_types:
            if src_entity is None:
                src_result = ec.gql_get_matching_entity_by_name(src_api_key, entity_type, entity_name,
                                                                src_account_id, src_region)
                if src_result['entityFound']:
                    src_entity = src_result['entity']
                    tag_status[entity_name][tgkeys.ENTITY_TYPE] = entity_type
                    tag_status[entity_name][tgkeys.SOURCE_FOUND] = True
                else:
                    logger.debug("No match found in source account for entity with name " + entity_name +
                                 " with type " + entity_type + ". Continuing to check other defined entity types")
        if src_entity is None:
            logger.error(
                "Skipping entity. Unable to find entity " + entity_name + " in source account " + str(src_account_id))
            tag_status[entity_name][tgkeys.SOURCE_FOUND] = False
            continue
        tgt_entity = None
        for entity_type in entity_types:
            if tgt_entity is None:
                tgt_result = ec.gql_get_matching_entity_by_name(tgt_api_key, entity_type, entity_name,
                                                                tgt_account_id, tgt_region)
                if tgt_result['entityFound']:
                    tgt_entity = tgt_result['entity']
                    tag_status[entity_name][tgkeys.ENTITY_TYPE] = entity_type
                    tag_status[entity_name][tgkeys.TARGET_FOUND] = True
                else:
                    logger.debug("No match found in target account for entity with name " + entity_name +
                                 " with type " + entity_type + ". Continuing to check other defined entity types")
        if tgt_entity is None:
            logger.error(
                "Skipping entity. Unable to find entity " + entity_name + " in target account " + str(tgt_account_id))
            tag_status[entity_name][tgkeys.TARGET_FOUND] = False
            continue
        tags_needed = ec.tags_diff(src_entity['tags'], tgt_entity['tags'])
        logger.info("Tags needed: " + str(tags_needed))
        if len(tags_needed) == 0:
            logger.info("Target entity " + tgt_entity['name'] + 'already contains all necessary tags')
            tag_status[entity_name][tgkeys.TAGS_NEEDED] = False
            continue
        tag_status[entity_name][tgkeys.TAGS_NEEDED] = tags_needed
        result = ec.gql_mutate_add_tags(tgt_api_key, tgt_entity['guid'], tags_needed, tgt_region)
        if 'error' in result:
            tag_status[entity_name][tgkeys.TAGS_ADDED] = False
            tag_status[entity_name][tgkeys.ERROR] = result['error']
            continue
        tag_status[entity_name][tgkeys.TAGS_ADDED] = True
    file_name = utils.file_name_from(from_file)
    status_csv = src_account_id + "_" + file_name + "_" + tgt_account_id + ".csv"
    store.save_status_csv(status_csv, tag_status, tgkeys)


def main():
    parser = configure_parser()
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source api key', 'ENV_SOURCE_API_KEY')
    src_region = utils.ensure_source_region(args)
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target api key', "ENV_TARGET_API_KEY")
    tgt_region = utils.ensure_target_region(args)
    entity_types = parse_entity_types(args)
    if len(entity_types) == 0:
        logger.error('At least one entity type must be specified. Currently supported: ' +
                     ec.SYNTH_MONITOR + ',' + ec.SYNTH_SECURE_CRED + ',' + ec.APM_APP + ',' + ec.BROWSER_APP + ',' + ec.DASHBOARDS + ',' + ec.INFRA_HOST + ',' + ec.INFRA_INT + ',' + ec.MOBILE_APP + ',' + ec.INFRA_LAMBDA)
        sys.exit()

    migrate_tags(args.fromFile[0], args.sourceAccount[0], src_region, source_api_key,
                 args.targetAccount[0], tgt_region, target_api_key, entity_types)


if __name__ == '__main__':
    main()