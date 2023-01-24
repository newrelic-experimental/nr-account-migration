import argparse
import os
import sys
import time
import library.clients.entityclient as ec
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate entity tags from one account to another')
    parser.add_argument('--sourceAccount', nargs=1, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='region us(default) or eu')
    parser.add_argument('--toFile', nargs=1, required=True, help='File to populate entity names. '
                                                                 'This will be created in output directory')
    parser.add_argument('--synthetics', dest='synthetics', required=False, action='store_true', help='Pass --synthetics to list matching Synthetic monitor entities')
    parser.add_argument('--securecreds', dest='securecreds', required=False, action='store_true', help='Pass --securecreds to list matching Synthetic secure credentials entities')
    parser.add_argument('--apm', dest='apm', required=False, action='store_true', help='Pass --apm to list matching APM application entities')
    parser.add_argument('--browser', dest='browser', required=False, action='store_true', help='Pass --browser to list matching Browser application entities')
    parser.add_argument('--dashboards', dest='dashboards', required=False, action='store_true', help='Pass --dashboards to list matching Dashboard entities')
    parser.add_argument('--infrahost', dest='infrahost', required=False, action='store_true', help='Pass --infrahost to list matching Infrastructure host entities')
    parser.add_argument('--infraint', dest='infraint', required=False, action='store_true', help='Pass --infraint to list matching Infrastructure integration entities')
    parser.add_argument('--mobile', dest='mobile', required=False, action='store_true', help='Pass --mobile to list matching Mobile application entities')
    parser.add_argument('--lambda', dest='lambda_function', required=False, action='store_true', help='Pass --lambda to list matching Lambda function entities')
    parser.add_argument('--workload', dest='workload', required=False, action='store_true',
                        help='Pass --workloads to list matching Workload entities')
    parser.add_argument('--tagName', nargs=1, required=False, help='(Optional) Tag name to use when filtering results. Required if --tagValue is passed.')
    parser.add_argument('--tagValue', nargs=1, required=False, help='(Optional) Tag value to use when filtering results. Required if --tagName is passed.')
    return parser


def print_params(args, source_api_key, entity_types, src_region):
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4])*"*"+source_api_key[-4:])
    logger.info("sourceRegion : " + src_region)
    logger.info("Using entity types : " + str(entity_types))
    if args.tagName:
        logger.info("Using tag name " + str(args.tagName[0]) + " and tag value " + str(args.tagValue[0]))
    if args.toFile:
        logger.info("Using toFile : " + args.toFile[0])


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
    if args.workload:
        entity_types.append(ec.WORKLOAD)
    return entity_types


def fetch_entities(src_account_id, src_api_key, entity_types, output_file, *,
                   tag_name=None, tag_value=None, src_region='us', assessment=None):
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
    entity_types = parse_entity_types(args)
    if len(entity_types) == 0:
        logger.error('At least one entity type must be specified. Currently supported: ' +
                            ec.SYNTH_MONITOR + ',' + ec.SYNTH_SECURE_CRED + ',' + ec.APM_APP + ',' + ec.BROWSER_APP + ',' + ec.DASHBOARDS + ',' + ec.INFRA_HOST + ',' + ec.INFRA_INT + ',' + ec.MOBILE_APP + ',' + ec.INFRA_LAMBDA)
        sys.exit()
    if args.tagName is not None and args.tagValue is None:
        logger.error('tagValue is required when tagName is set')
        sys.exit()
    if args.tagValue is not None and args.tagName is None:
        logger.error('tagName is required when tagValue is set')
        sys.exit()
    src_region = utils.ensure_source_region(args)
    print_params(args, src_api_key, entity_types, src_region)
    if args.tagName is None:
        fetch_entities(args.sourceAccount[0], src_api_key, entity_types, args.toFile[0], src_region=src_region, assessment=args.assessment)
    else:
        fetch_entities(args.sourceAccount[0], src_api_key, entity_types, args.toFile[0], tag_name=args.tagName[0],
                       tag_value=args.tagValue[0], src_region=src_region, assessment=args.assessment)
    

if __name__ == '__main__':
    main()
