import argparse
import os
import json
import library.migrationlogger as nrlogger
import library.clients.notificationsclient as notificationsclient
import library.localstore as store
import library.utils as utils

logger = nrlogger.get_logger(os.path.basename(__file__))
nc = notificationsclient.NotificationsClient()


def configure_parser():
    parser = argparse.ArgumentParser(description='Fetch and store notifications')
    parser.add_argument('--account', nargs=1, type=str, required=False, help='Account ID')
    parser.add_argument('--accounts', nargs=1, type=str, required=False, help='Path to file with account IDs')
    parser.add_argument('--userApiKey', nargs=1, type=str, required=True, help='User API Key')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--destinations', dest='destinations', required=False, action='store_true', help='Query destinations')
    parser.add_argument('--channels', dest='channels', required=False, action='store_true', help='Query channels')
    return parser


def fetch_destinations(user_api_key, account_id, region, accounts_file=None):
    destinations_by_id = get_config(nc.destinations, user_api_key, account_id, region, accounts_file)
    return destinations_by_id


def fetch_channels(user_api_key, account_id, region, accounts_file=None):
    channels_by_id = get_config(nc.channels, user_api_key, account_id, region, accounts_file)
    return channels_by_id


def get_config(func, user_api_key, account_id, region, accounts_file):
    acct_ids = []
    if account_id: 
        acct_ids = [account_id]
    else:
        acct_ids = store.load_names(accounts_file)
    configs_by_id = {}
    # Strip the class name
    field = func.__name__
    for acct_id in acct_ids:
        done = False
        cursor = None
        while not done:
            try:
                response = nc.query(func, user_api_key, int(acct_id), region, cursor)
                logger.debug(json.dumps(response))
                config = response['response']['data']['actor']['account']['aiNotifications'][field]['entities']
                cursor = response['response']['data']['actor']['account']['aiNotifications'][field]['nextCursor']
                if ('error' in response):
                    logger.error(f'Could not fetch destinations for account {acct_id}')
                    logger.error(response['error'])
                    break
                error = response['response']['data']['actor']['account']['aiNotifications'][field]['error']
                if (error is not None):
                    logger.error(f'Could not fetch destinations for account {acct_id}')
                    logger.error(error)
                    break
                if cursor is None:
                    done = True
            except:
                logger.error(f'Error querying {field} for account {acct_id}')
            else:
                account_configs_by_id = {}
                for element in config:
                    element['accountId'] = acct_id
                    configs_by_id.setdefault(element['id'], element)
                    account_configs_by_id.setdefault(element['id'], element)
        if field == 'destinations':
            store.save_notification_destinations(acct_id, account_configs_by_id)
        if field == 'channels':
            store.save_notification_channels(acct_id, account_configs_by_id)
    logger.info(configs_by_id)
    store.save_config_csv(field, configs_by_id)
    return configs_by_id


def main():
    parser = configure_parser()
    args = parser.parse_args()
    user_api_key = utils.ensure_user_api_key(args)
    if not user_api_key:
        utils.error_and_exit('userApiKey', 'ENV_USER_API_KEY')
    region = utils.ensure_region(args)
    account_id = args.account[0] if args.account else None
    accounts_file = args.accounts[0] if args.accounts else None
    if args.destinations:
        fetch_destinations(user_api_key, account_id, region, accounts_file)
    elif args.channels:
        fetch_channels(user_api_key, account_id, region, accounts_file)
    else:
        logger.info("pass [--destinations | --channels] to fetch configuration")


if __name__ == '__main__':
    main()