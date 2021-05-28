import argparse
import os
import time
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.clients.alertsclient as ac
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(
        description='Fetch and store a map from application entities to alert policy and '
                    'from alert policies to application entity')
    parser.add_argument('--sourceAccount', type=str, nargs=1, required=True, help='Source accountId to store the map')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--sourceApiKey', type=str, nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--useLocal', dest='useLocal', required=False, action='store_true',
                        help='By default policies are fetched. Pass this to use policies pre-fetched by store_policies.')
    return parser


def print_params(args, src_api_key, src_region):
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    if args.sourceRegion and len(args.sourceRegion) > 0:
        logger.info("sourceRegion : " + args.sourceRegion[0])
    else:
        logger.info("sourceRegion not passed : Defaulting to " + src_region)
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4]) * "*" + src_api_key[-4:])
    logger.info("Using useLocal : " + str(args.useLocal))


def find_policy_name(policies, policy_id):
    for policy in policies:
        if policy.id == policy_id:
            return policy.name


def store_policy_entity_map(src_api_key, src_account_id, src_region, use_local):
    if use_local:
        logger.info('Loading alert policies from local...')
        all_policies = store.load_alert_policies(src_account_id)
    else:
        logger.info('Fetching and storing alert policies...')
        all_policies = ac.get_all_alert_policies(src_api_key, src_region)
    if 'response_count' not in all_policies or all_policies['response_count'] == 0:
        logger.info('No policies found for account ID %s' % str(src_account_id))
        return
    logger.info('%d policies loaded. Mapping app entity conditions for account ID %s.' %
                (all_policies['response_count'], src_account_id))
    policy_entity_map = ac.get_policy_entity_map(src_api_key, all_policies['policies'], src_region)
    store.save_alert_policy_entity_map(src_account_id, policy_entity_map)


def main():
    print(logger)
    start_time = time.time()
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    if not src_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    src_region = utils.ensure_source_region(args)
    print_params(args, src_api_key, src_region)
    store_policy_entity_map(src_api_key, args.sourceAccount[0], src_region, args.useLocal)
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")


if __name__ == '__main__':
    main()