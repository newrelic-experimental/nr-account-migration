import argparse
import os
import json
import library.migrationlogger as nrlogger
import library.clients.workflowsclient as workflowsclient
import library.localstore as store
import library.utils as utils

logger = nrlogger.get_logger(os.path.basename(__file__))
wc = workflowsclient.WorkflowsClient()


def configure_parser():
    parser = argparse.ArgumentParser(description='Fetch and store workflows')
    parser.add_argument('--account', nargs=1, type=str, required=False, help='Account ID')
    parser.add_argument('--accounts', nargs=1, type=str, required=False, help='Path to file with account IDs')
    parser.add_argument('--userApiKey', nargs=1, type=str, required=True, help='User API Key')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    return parser


def fetch_workflows(user_api_key, account_id, region, accounts_file=None):
    workflow_by_source_id = get_config(wc.workflows, user_api_key, account_id, region, accounts_file)
    store.save_workflows(account_id, workflow_by_source_id)
    return workflow_by_source_id


def get_config(func, user_api_key, account_id, region, from_file):
    acct_ids = []
    if account_id: 
        acct_ids = [account_id]
    else:
        acct_ids = store.load_names(from_file)
    configs_by_id = {}
    # Strip the class name
    field = func.__name__
    for acct_id in acct_ids:
        done = False
        cursor = None
        while not done:
            try:
                response = wc.query(func, user_api_key, int(acct_id), region, cursor)
                logger.debug(json.dumps(response))
                config = response['response']['data']['actor']['account']['aiWorkflows'][field]['entities']
                cursor = response['response']['data']['actor']['account']['aiWorkflows'][field]['nextCursor']
                if ('error' in response):
                    logger.error(f'Could not fetch workflows for account {acct_id}')
                    logger.error(response['error'])
                    break
                # No error attribute for aiWorkflows
                if cursor is None:
                    done = True
            except:
                logger.error(f'Error querying {field} for account {acct_id}')
            else:
                for element in config:
                    element['accountId'] = acct_id
                    configs_by_id.setdefault(element['id'], element)
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
    fetch_workflows(user_api_key, args.account[0], args.accounts[0], region)


if __name__ == '__main__':
    main()