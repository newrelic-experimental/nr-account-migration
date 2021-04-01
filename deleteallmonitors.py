import argparse
import sys
import os
import requests
import time
import library.localstore as localstore
import library.migrationlogger as migrationlogger
import library.clients.monitorsclient as monitorsclient


# This script has been built for TESTING purpose only. Use at your own risk.
# Remember it will DELETE all monitors in an account with no way of reverting it back.
# Well a backup has been added and will be saved under db/<accountId>/monitors/timeStamp-backup
# This can be used to restore the monitors back to targetAccount using migratemonitors.
# Example use same account id for source and target
# deleteallmonitors deletes all the monitors in the targetAccount
logger = migrationlogger.get_logger(os.path.basename(__file__))
headers = {}
monitors_url = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/'
parser = argparse.ArgumentParser(description='Delete Monitors from an account')
from_api_key = ""


def setup_params():
    parser.add_argument('--targetApiKey', type=str, nargs=1, required=False, help='API Key for the account')
    parser.add_argument('--targetAccount', type=str, nargs=1, required=True, help='Target account')


def print_args():
    logger.info("Using targetApiKey : " + len(args.targetApiKey[0][:-4])*"*"+args.targetApiKey[0][-4:])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))


def setup_headers(api_key):
    if api_key:
        target_api_key = api_key
    else:
        target_api_key = os.environ.get('ENV_TARGET_API_KEY')
    headers['Api-Key'] = target_api_key
    if not headers['Api-Key']:
        logger.error('Error: Missing API Key. either pass as param ---targetApiKey or \
            environment variable ENV_TARGET_API_KEY.\n \
            e.g. export ENV_TARGET_API_KEY="NRNA7893asdfhkh"')
        sys.exit()


def delete(monitors, target_acct):
    success_status = {}
    failure_status = {}
    for monitor in monitors:
        delete_monitor(monitor, target_acct, failure_status,  success_status)
    return {'success': success_status, 'failure': failure_status}


def delete_monitor(monitor, target_acct, failure_status, success_status):
    monitor_id = monitor['id']
    monitor_name = monitor['name']
    response = requests.delete(monitors_url + monitor_id, headers=headers)
    if response.status_code == 204:
        success_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
        logger.info(target_acct + ":" + monitor_name + ":" + str(success_status[monitor_name]))
    else:
        failure_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
        logger.info(target_acct + ":" + monitor_name + ":" + str(failure_status[monitor_name]))
    # trying to stay within 3 requests per second
    time.sleep(0.3)


def delete_all_monitors(api_key, target_acct):
    setup_headers(api_key)
    all_monitors_def_json = monitorsclient.fetch_all_monitors(api_key)
    timestamp = time.strftime("%Y-%m%d-%H%M%S") + "-bakup"
    storage_dir = localstore.create_storage_dirs(target_acct, timestamp)
    monitor_names_file = localstore.create_output_file("monitors-" + timestamp + ".csv")
    with monitor_names_file.open('a') as monitor_names_out:
        for monitor_def_json in all_monitors_def_json:
            monitor_json = {'definition': monitor_def_json}
            monitor_name = localstore.sanitize(monitor_def_json['name'])
            monitor_names_out.write(monitor_name + "\n")
            localstore.save_monitor_to_file(monitor_name, storage_dir, monitor_json)
    logger.info("Backed up %d monitors in %s before deleting", len(all_monitors_def_json), storage_dir)
    del_response = delete(all_monitors_def_json, target_acct)
    logger.debug(del_response)


if __name__ == '__main__':
    start_time = time.time()
    setup_params()
    args = parser.parse_args()
    print_args()
    delete_all_monitors(args.targetApiKey[0], args.targetAccount[0])
    logger.info("Time taken : " + str(time.time() - start_time) + " seconds.")
