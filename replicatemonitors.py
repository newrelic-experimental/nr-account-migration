import argparse
import os
import sys
import time
import library.localstore as localstore
import library.migrationlogger as migrationlogger
import library.monitortypes as monitortypes
import library.clients.monitorsclient as monitorsclient

# TESTING only replicatemonitors must be used after doing a fetchmonitors
# specify the source account, timestamp that you want to migrate
# Also specify the targetAccount and targetApiKey to which you want to migrate the stored monitors
# This script creates multiple copies of the source monitors. Used for generating test data

logger = migrationlogger.get_logger(os.path.basename(__file__))
target_api_key = ''
monitors_url = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/'
parser = argparse.ArgumentParser(description='Replicate multiple copies of Synthetic Monitors')


def setup_params():
    parser.add_argument('--fromFile', type=str, nargs=1, required=True, help='Path to file with monitor names')
    parser.add_argument('--sourceAccount', type=int, nargs=1, required=True, help='Source accountId \
    local Store db/<sourceAccount>/monitors of this account will be used.')
    parser.add_argument('--targetAccount', type=int, nargs=1, required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', type=str, nargs=1, required=False, help='Target API Key, \
    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--timeStamp', type=str, nargs=1, required=True, help='timeStamp to migrate')
    parser.add_argument('--copies', type=int, nargs=1, required=True, help='How many copies of existing monitors')


def print_args():
    logger.info("Using fromFile : " + str(args.fromFile[0]))
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using targetApiKey : " + target_api_key)
    logger.info("Using timeStamp : " + args.timeStamp[0])
    logger.info("Creating Copies : " + str(args.copies[0]))


def setup_headers():
    global target_api_key
    if args.targetApiKey:
        target_api_key = args.targetApiKey[0]
    else:
        target_api_key = os.environ.get('ENV_TARGET_API_KEY')
    if not target_api_key:
        logger.error('Error: Missing param targetApiKey or env variable ENV_TARGET_API_KEY .\n \
        e.g. export ENV_TARGET_API_KEY="NRAA7893asdfhkh" or pass as param')
        sys.exit()


def replicate(all_monitors_json, copies):
    monitor_status = {}
    all_monitor_labels = localstore.load_monitor_labels(args.sourceAccount[0])
    for monitor_json in all_monitors_json:
        orig_monitor_name = monitor_json['definition']['name']
        source_monitor_id = monitor_json['definition']['id']
        monitor_labels = []
        if len(all_monitor_labels) > 0 and source_monitor_id in all_monitor_labels:
            monitor_labels = all_monitor_labels[source_monitor_id]
        for copy in range(copies):
            monitor_name = orig_monitor_name + str(copy + 1)
            logger.info('creating ' + monitor_name)
            monitor_json['definition']['name'] = monitor_name
            monitorsclient.post_monitor_definition(target_api_key, monitor_name, monitor_json, monitor_status)
            if monitortypes.is_scripted(monitor_json['definition']):
                if 'script' in monitor_json:
                    monitorsclient.put_script(target_api_key, monitor_json, monitor_name, monitor_status)
            monitorsclient.apply_labels(target_api_key, monitor_labels, monitor_name, monitor_status)
            logger.debug(monitor_status[monitor_name])
            # trying to stay within 3 requests per second
            # we are assuming it will take around 500 ms to process 3 requests
            time.sleep(0.5)
    return monitor_status


def replicate_monitors():
    monitor_names = localstore.load_names(args.fromFile[0])
    logger.debug(monitor_names)
    all_monitors_json = localstore.load_monitors(args.sourceAccount[0], args.timeStamp[0], monitor_names)
    monitor_status = replicate(all_monitors_json, args.copies[0])
    logger.debug(monitor_status)


setup_params()
args = parser.parse_args()
setup_headers()
print_args()
replicate_monitors()