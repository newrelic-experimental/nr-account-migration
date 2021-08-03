import argparse
import sys
import os
import requests
import time
import library.localstore as store
import library.migrationlogger as m_logger
import library.utils as utils
import library.clients.monitorsclient as monitorsclient


# deletemonitors deletes a list of monitors provided in one per line in a csv file
# monitors must have been pre-feteched using fetchmonitors and stored in db/<target_account_id>/monitors/<time_stamp>
# The fromFile, targetAccountId, targetApiKey and timeStamp must be specified
logger = m_logger.get_logger(os.path.basename(__file__))
headers = {}
from_api_key = ""


def configure_parser():
    parser = argparse.ArgumentParser(description='Delete Monitors from an account')
    parser.add_argument('--fromFile', nargs=1, required=True, help='Path to file with monitor names, one per line')
    parser.add_argument('--targetApiKey', nargs=1, required=False, help='API Key for the account')
    parser.add_argument('--targetAccount', nargs=1, required=True, help='Target account')
    parser.add_argument('--timeStamp', nargs=1, required=True, help='Timestamp of the pre-fetched monitors')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='region us(default) or eu')
    return parser


def print_args(args, region):
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using targetApiKey : " + args.targetApiKey[0])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using timeStamp : " + args.timeStamp[0])
    logger.info("region : " + region)


def delete(monitor_definitions, target_account, tgt_api_key, region):
    success_status = {}
    failure_status = {}
    for monitor_definition in monitor_definitions:
        monitorsclient.delete_monitor(monitor_definition['definition'], target_account, failure_status, success_status,
                                      tgt_api_key, region)
    return {'success': success_status, 'failure': failure_status}


def delete_monitors(from_file, tgt_account, time_stamp, tgt_api_key, region):
    monitor_names = store.load_names(from_file)
    monitor_definitions = store.load_monitors(tgt_account, time_stamp, monitor_names)
    del_response = delete(monitor_definitions, tgt_account, tgt_api_key, region)
    logger.debug(del_response)


def main():
    start_time = time.time()
    parser = configure_parser()
    args = parser.parse_args()
    region = utils.ensure_region(args)
    tgt_api_key = utils.ensure_target_api_key(args)
    print_args(args, region)
    delete_monitors(args.fromFile[0], args.targetAccount[0], args.timeStamp[0], tgt_api_key, region)
    logger.info("Time taken : " + str(time.time() - start_time) + " seconds.")


if __name__ == '__main__':
    main()
