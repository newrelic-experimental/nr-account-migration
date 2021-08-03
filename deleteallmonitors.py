import argparse
import sys
import os
import requests
import time
import library.localstore as localstore
import library.migrationlogger as migrationlogger
import library.clients.monitorsclient as monitorsclient
import library.utils as utils
from library.clients.endpoints import Endpoints


# This script has been built for TESTING purpose only. Use at your own risk.
# Remember it will DELETE all monitors in an account with no way of reverting it back.
# Well a backup has been added and will be saved under db/<accountId>/monitors/timeStamp-backup
# This can be used to restore the monitors back to targetAccount using migratemonitors.
# Example use same account id for source and target
# deleteallmonitors deletes all the monitors in the targetAccount
logger = migrationlogger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Delete Monitors from an account')
    parser.add_argument('--targetApiKey', type=str, nargs=1, required=False, help='API Key for the account')
    parser.add_argument('--targetAccount', type=str, nargs=1, required=True, help='Target account')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='region us(default) or eu')
    return parser


def print_args(args, region):
    logger.info("Using targetApiKey : " + len(args.targetApiKey[0][:-4])*"*"+args.targetApiKey[0][-4:])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("region : " + region)


def delete(monitors, target_acct, tgt_api_key, region):
    success_status = {}
    failure_status = {}
    for monitor in monitors:
        monitorsclient.delete_monitor(monitor, target_acct, failure_status,  success_status, tgt_api_key, region)
    return {'success': success_status, 'failure': failure_status}


def delete_all_monitors(api_key, target_acct, region):
    all_monitors_def_json = monitorsclient.fetch_all_monitors(api_key, region)
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
    del_response = delete(all_monitors_def_json, target_acct, api_key, region)
    logger.debug(del_response)


def main():
    start_time = time.time()
    parser = configure_parser()
    args = parser.parse_args()
    region = utils.ensure_region(args)
    tgt_api_key = utils.ensure_target_api_key(args)
    print_args(args, region)
    delete_all_monitors(tgt_api_key, args.targetAccount[0], region)
    logger.info("Time taken : " + str(time.time() - start_time) + " seconds.")


if __name__ == '__main__':
    main()
