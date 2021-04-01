import argparse
import sys
import os
import requests
import time
import library.localstore as store
import library.migrationlogger as m_logger


# deletemonitors deletes a list of monitors provided in one per line in a csv file
# monitors must have been pre-feteched using fetchmonitors and stored in db/<target_account_id>/monitors/<time_stamp>
# The fromFile, targetAccountId, targetApiKey and timeStamp must be specified
logger = m_logger.get_logger(os.path.basename(__file__))
headers = {}
monitors_url = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/'
parser = argparse.ArgumentParser(description='Delete Monitors from an account')
from_api_key = ""


def setup_params():
    parser.add_argument('--fromFile', nargs=1, required=True, help='Path to file with monitor names, one per line')
    parser.add_argument('--targetApiKey', nargs=1, required=False, help='API Key for the account')
    parser.add_argument('--targetAccount', nargs=1, required=True, help='Target account')
    parser.add_argument('--timeStamp', nargs=1, required=True, help='Timestamp of the pre-fetched monitors')


def print_args():
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using targetApiKey : " + args.targetApiKey[0])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using timeStamp : " + args.timeStamp[0])


def setup_headers():
    if args.targetApiKey:
        target_api_key = args.targetApiKey[0]
    else:
        target_api_key = os.environ.get('ENV_TARGET_API_KEY')
    headers['Api-Key'] = target_api_key
    if not headers['Api-Key']:
        logger.error('Error: Missing API Key. either pass as param ---targetApiKey or \
            environment variable ENV_TARGET_API_KEY.\n \
            e.g. export ENV_TARGET_API_KEY="NRNA7893asdfhkh"')
        sys.exit()


def delete(monitors):
    success_status = {}
    failure_status = {}
    for monitor in monitors:
        monitor_id = monitor['definition']['id']
        monitor_name = monitor['definition']['name']
        target_account = str(args.targetAccount[0])
        response = requests.delete(monitors_url + monitor_id, headers=headers)
        if response.status_code == 204:
            success_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
            logger.info(target_account + ":" + monitor_name + ":" + str(success_status[monitor_name]))
        else:
            failure_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
            logger.info(target_account + ":" + monitor_name + ":" + str(failure_status[monitor_name]))
        # trying to stay within 3 requests per second
        time.sleep(0.5)
    return {'success': success_status, 'failure': failure_status}


def delete_monitors():
    monitor_names = store.load_names(args.fromFile[0])
    monitors = store.load_monitors(args.targetAccount[0], args.timeStamp[0], monitor_names)
    del_response = delete(monitors)
    logger.debug(del_response)


start_time = time.time()
setup_params()
args = parser.parse_args()
setup_headers()
print_args()
delete_monitors()
logger.info("Time taken : " + str(time.time() - start_time) + " seconds.")
