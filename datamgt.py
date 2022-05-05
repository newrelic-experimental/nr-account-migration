import argparse
import os
import json
import library.migrationlogger as nrlogger
import library.clients.datamgtclient as datamgtclient
import library.localstore as store
import library.utils as utils

logger = nrlogger.get_logger(os.path.basename(__file__))
dmc = datamgtclient.DataManagementClient()


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate Dashboards')
    parser.add_argument('--accounts', nargs=1, type=str, required=True, help='Path to file with account IDs')
    parser.add_argument('--userApiKey', nargs=1, type=str, required=True, help='User API Key')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--featureSettings', dest='featureSettings', required=False, action='store_true',
                        help='Query Feature Settings')
    return parser


def get_feature_settings(user_api_key, from_file, region):
    acct_ids = store.load_names(from_file)
    feature_settings = [['accountId', 'key','name', 'enabled']]
    for acct_id in acct_ids:
        result = dmc.get_feature_settings(user_api_key, int(acct_id), region)
        logger.info(json.dumps(result))
        for featureSetting in result['response']['data']['actor']['account']['dataManagement']['featureSettings']:
            feature_settings.append([acct_id, featureSetting['key'], featureSetting['name'], featureSetting['enabled']])
    logger.info(feature_settings)
    store.save_feature_settings_csv(feature_settings)




def main():
    parser = configure_parser()
    args = parser.parse_args()
    user_api_key = utils.ensure_user_api_key(args)
    if not user_api_key:
        utils.error_and_exit('userApiKey', 'ENV_USER_API_KEY')
    region = utils.ensure_region(args)
    if args.featureSettings:
        get_feature_settings(user_api_key, args.accounts[0], region)
    else:
        logger.info("pass --featureSettings to fetch featureSettings")


if __name__ == '__main__':
    main()