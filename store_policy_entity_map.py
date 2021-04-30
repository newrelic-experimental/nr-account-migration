import argparse
import os
import time
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.clients.alertsclient as ac
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))

def setup_params(parser):
    parser.add_argument('--sourceAccount', type=str, nargs=1, required=True, help='Source accountId to store the map')
    parser.add_argument('--sourceApiKey', type=str, nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--useLocal', dest='useLocal', required=False, action='store_true',
                        help='By default policies are fetched. Pass this to use policies pre-fetched by store_policies.')

def print_params(args):
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4]) * "*" + source_api_key[-4:])
    logger.info("Using useLocal : " + str(args.useLocal))

def find_policy_name(policies, policy_id):
    for policy in policies:
        if policy.id == policy_id:
            return policy.name

def store_policy_entity_map(src_api_key, src_account_id, use_local):
    if use_local:
        logger.info('Loading alert policies from local...')
        all_policies = store.load_alert_policies(src_account_id)
    else:
        logger.info('Fetching and storing alert policies...')
        all_policies = ac.get_all_alert_policies(src_api_key)
    
    if not 'response_count' in all_policies or all_policies['response_count'] == 0:
        logger.info('No policies found for account ID %s' % str(src_account_id))
        return

    logger.info('%d policies loaded. Mapping app entity conditions for account ID %s.' % (all_policies['response_count'], src_account_id))

    policy_entity_map = ac.get_policy_entity_map(src_api_key, all_policies['policies'])
    store.save_alert_policy_entity_map(src_account_id, policy_entity_map)

if __name__ == '__main__':
    print(logger)
    start_time = time.time()
    parser = argparse.ArgumentParser(description='Fetch and store a map from application entities to alert policy and from alert policies to application entity')
    setup_params(parser)
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    print_params(args)
    store_policy_entity_map(source_api_key, args.sourceAccount[0], args.useLocal)
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")