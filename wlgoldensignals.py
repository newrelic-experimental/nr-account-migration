import argparse
import os
import json
import library.utils as utils
import library.migrationlogger as logger
import library.clients.entityclient as ec
import library.clients.goldensignals as goldensignals
import library.localstore as store

logger = logger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Workload Golden Signal Mutations')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--tagName', nargs=1, required=False, help='Tag name to lookup workloads.')
    parser.add_argument('--tagValue', nargs=1, required=False, help='Tag value to lookup workloads.')
    parser.add_argument('--goldenSignalsJson', nargs=1, required=False, help='JSON defining golden signal  metrics '
                                                                             'stored in ./goldensignals')
    parser.add_argument('--resetGoldenSignals', dest='resetGoldenSignals', required=False, action='store_true',
                        help='Reset golden signals.')
    parser.add_argument('--domain', nargs=1, required=False, help='Needed for resetGoldenSignals. Domain for context '
                                                                  'e.g. APM | BROWSER | INFRA | MOBILE | SYNTH | EXT')
    parser.add_argument('--type', nargs=1, required=False, help='Needed for resetGoldenSignals. type for context e.g. '
                                                                'APPLICATION | DASHBOARD | HOST | MONITOR | WORKLOAD')

    return parser


def print_args(args, target_api_key, target_region):
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using targetApiKey : " + len(target_api_key[:-4])*"*"+target_api_key[-4:])
    logger.info("target region : " + target_region)
    if args.goldenSignalsJson:
        logger.info("Will apply Golden Signal Override using metrics in " + args.goldenSignalsJson[0])
    if args.resetGoldenSignals:
        logger.info("Will reset Golden Signals")
    if args.tagName and args.tagValue:
        logger.info("For Workloads with " + args.tagName[0] + "=" + args.tagValue[0])
    if args.domain:
        logger.info("Using domain " + args.domain[0])
    if args.type:
        logger.info("Using type " + args.domain[0])


def override_golden_signals(target_account, target_api_key, wl_tag_name, wl_tag_value, golden_signals_json,
                            target_region):
    logger.info("Applying golden signal overrides")
    logger.info("Loading golden signal metrics from " + golden_signals_json)
    wl_metrics = store.load_json_from_file("goldensignals", golden_signals_json)
    if 'metrics' not in wl_metrics:
        utils.error_message_and_exit("Could not load metrics from " + golden_signals_json)
    logger.info("Fetching workloads matching " + wl_tag_name + "=" + wl_tag_value)
    result = ec.gql_get_entities_by_type(target_api_key, ec.WORKLOAD, target_account,
                                         wl_tag_name, wl_tag_value, target_region)
    if 'errors' in result:
        utils.error_message_and_exit("Error Fetching workloads matching " + wl_tag_name + "=" + wl_tag_value + " : " +
                                     json.dumps(result['errors']))
    if 'entities' in result and len(result['entities']) == 0:
        utils.error_message_and_exit("No workloads matching " + wl_tag_name + "=" + wl_tag_value)
    goldenSignals = goldensignals.GoldenSignals(target_region)
    for workload in result['entities']:
        logger.info('Overriding ' + workload['name'] + ':' + workload['guid'])
        goldenSignals.override(target_api_key, workload['guid'], wl_metrics['domain'], wl_metrics['type'],
                               wl_metrics['metrics'])


def reset_golden_signals(target_account, target_api_key, wl_tag_name, wl_tag_value, target_region):
    logger.info("Resetting golden signals")
    result = ec.gql_get_entities_by_type(target_api_key, ec.WORKLOAD, target_account, wl_tag_name, wl_tag_value,
                                         target_region)
    goldenSignals = goldensignals.GoldenSignals(target_region)
    for workload in result['entities']:
        logger.info('Resetting ' + workload['name'] + ':' + workload['guid'])
        result = goldenSignals.reset(target_api_key, workload['guid'], 'INFRA', 'HOST' )
        logger.info(json.dumps(result))


def main():
    parser = configure_parser()
    args = parser.parse_args()
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target api key', 'ENV_TARGET_API_KEY')
    target_region = utils.ensure_target_region(args)
    if not args.goldenSignalsJson and not args.resetGoldenSignals:
        utils.error_message_and_exit("Either --goldenSignalsJson or --resetGoldenSignals must be passed")
    if args.goldenSignalsJson and args.resetGoldenSignals:
        utils.error_message_and_exit("Only one of --goldenSignalsJson or --resetGoldenSignals must be passed")
    if args.goldenSignalsJson and not (args.tagName and args.tagValue):
        utils.error_message_and_exit("tagName and tagValue are required to look up workloads "
                                     "and apply goldenSignalsJson")
    if args.resetGoldenSignals and not (args.tagName and args.tagValue):
        utils.error_message_and_exit("tagName and tagValue are required to look up workloads to resetGoldenSignals")
    if args.resetGoldenSignals and not (args.domain or args.type):
        utils.error_message_and_exit("domain and type are required to set context for override signals")
    print_args(args, target_api_key, target_region)
    if args.goldenSignalsJson:
        override_golden_signals(args.targetAccount[0], target_api_key, args.tagName[0], args.tagValue[0], 
                                args.goldenSignalsJson[0], target_region)
    elif args.resetGoldenSignals:
        reset_golden_signals(args.targetAccount[0], target_api_key, args.tagName[0], args.tagValue[0], target_region)


if __name__ == '__main__':
    main()
