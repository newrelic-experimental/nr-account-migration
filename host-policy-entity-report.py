import argparse
import os
import sys
import time
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
#import library.localstore as store
import library.migrationlogger as migrationlogger
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Generate report on policies mapped to conditions and entities.')
    parser.add_argument('--sourceAccount', nargs=1, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='region us(default) or eu')
    parser.add_argument('--toFile', nargs=1, required=True, help='File to populate entity names. '
                                                                 'This will be created in output directory')
    return parser


def print_params(args, source_api_key, src_region):
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4])*"*"+source_api_key[-4:])
    if args.sourceRegion and len(args.sourceRegion) > 0:
        logger.info("region : " + args.sourceRegion[0])
    else:
        logger.info("region not passed : Defaulting to " + src_region)
    if args.toFile:
        logger.info("Using toFile : " + args.toFile[0])


#def parse_entity_types(args):
#    entity_types = []
#    if args.synthetics:
#        entity_types.append(ec.SYNTH_MONITOR)
#    if args.apm:
#        entity_types.append(ec.APM_APP)
#    if args.browser:
#        entity_types.append(ec.BROWSER_APP)
#    if args.infrahost:
#        entity_types.append(ec.INFRA_HOST)
#    if args.mobile:
#        entity_types.append(ec.MOBILE_APP)
#    return entity_types


def fetch_entities(src_account_id, src_api_key, entity_types, output_file, *,
                   tag_name=None, tag_value=None, src_region='us'):
    entity_names = []
    for entity_type in entity_types:
        entities = ec.gql_get_entities_by_type(src_api_key, entity_type, src_account_id, tag_name, tag_value, src_region)
        for entity in entities['entities']:
            entity_names.append(entity['name'])
    entity_names_file = store.create_output_file(output_file)
    with entity_names_file.open('a') as entity_names_out:
        for entity_name in entity_names:
            name = store.sanitize(entity_name)
            entity_names_out.write(name + "\n")
        entity_names_out.close()
        logger.info("Wrote %s entities to file %s",len(entity_names), output_file)


def main():
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    if not src_api_key:
        utils.error_and_exit('source api key', 'ENV_SOURCE_API_KEY')
    src_region = utils.ensure_source_region(args)
    if not src_region:
        src_region = 'us'
    print_params(args, src_api_key, src_region)
    _policy_results = ac.get_all_alert_policies(src_api_key)
    policies = _policy_results['policies']
    for policy in policies:
        _condition_results = ac.get_infra_conditions(src_api_key, policy['id'], src_region)
        policy['conditions'] = []
        if 'conditions' in _condition_results:
            for condition in _condition_results['conditions']:
                policy['conditions'].append({'name': condition['name'], 'entities': condition['entities'] if 'entities' in condition else []})
            policy['conditions'] = _condition_results['conditions']
        elif 'data' in _condition_results:
            for condition in _condition_results['data']:
                policy['conditions'].append({'name': condition['name'], 'entities': condition['entities'] if 'entities' in condition else []})
                


        print(policy)
    


if __name__ == '__main__':
    main()
