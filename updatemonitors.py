import argparse
import sys
import os
import library.localstore as localstore
import library.migrationlogger as migrationlogger
import library.clients.monitorsclient as monitorsclient
import library.status.updatestatus as updatestatus
import library.utils as utils


logger = migrationlogger.get_logger(os.path.basename(__file__))


def setup_params(parser):
    parser.add_argument('--fromFile', nargs=1, required=True, help='Path to file with monitor names, one per line')
    parser.add_argument('--targetApiKey', nargs=1, required=False, help='API Key for the account')
    parser.add_argument('--targetAccount', nargs=1, required=True, help='Target account')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--timeStamp', nargs=1, required=True, help='Timestamp of the pre-fetched monitors')
    parser.add_argument('--renamePrefix', nargs=1, required=False, help='Pass prefix to rename monitors')
    parser.add_argument('--disable', dest='disable', required=False, action='store_true', help='Pass --disable to disable the monitors')
    parser.add_argument('--enable', dest='enable', required=False, action='store_true', help='Pass --enable to enable the monitors')


def ensure_target_api_key(args):
    if args.targetApiKey:
        api_key = args.targetApiKey[0]
    else:
        api_key = os.environ.get('ENV_TARGET_API_KEY')
    if not api_key:
        logger.error('Error: Missing param targetApiKey or env variable ENV_TARGET_API_KEY .\n \
        e.g. export ENV_TARGET_API_KEY="NRAA7893asdfhkh" or pass as param')
        sys.exit(1)
    return api_key


def print_args(args, tgt_region):
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using targetApiKey : " + args.targetApiKey[0])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("targetRegion : " + tgt_region)
    logger.info("Using timeStamp : " + args.timeStamp[0])
    if args.renamePrefix:
        logger.info("Monitors will be prefixed with : " + args.renamePrefix[0])
    if args.targetApiKey:
        logger.info("Using targetApiKey: " + len(args.targetApiKey[0][:-4]) * "*"
                    + args.targetApiKey[0][-4:])
    if args.disable:
        logger.info("Disable Monitors : " + str(args.disable))
    if args.enable:
        logger.info("Enable Monitors : " + str(args.enable))


def update_monitors(api_key, account_id, from_file, time_stamp, prefix, disable_flag, enable_flag, tgt_region):
    update_list = localstore.load_names(from_file)
    all_monitors = localstore.load_monitors(account_id, time_stamp, update_list)
    all_monitor_status = {}
    for monitor in all_monitors:
        monitor_id = monitor['definition']['id']
        monitor_name = monitor['definition']['name']
        update_json = {}
        all_monitor_status[monitor_name] = {}
        if prefix:
            new_name = prefix + monitor_name
            update_json['name'] = new_name
            all_monitor_status[monitor_name][updatestatus.UPDATED_NAME] = new_name
        if disable_flag:
            update_json['status'] = 'DISABLED'
            all_monitor_status[monitor_name][updatestatus.UPDATED_STATUS] = 'DISABLED'
        if enable_flag:
            update_json['status'] = 'ENABLED'
            all_monitor_status[monitor_name][updatestatus.UPDATED_STATUS] = 'ENABLED'
        result = monitorsclient.update(api_key, monitor_id, update_json, monitor_name, tgt_region)
        update_status(all_monitor_status, monitor_name, result)
    update_status_csv = str(account_id) + "_" + utils.file_name_from(from_file) + "_updated_monitors.csv"
    localstore.save_status_csv(update_status_csv, all_monitor_status, updatestatus)


def update_status(all_monitor_status, monitor_name, result):
    all_monitor_status[monitor_name][updatestatus.STATUS] = result['status']
    if 'error' in result:
        all_monitor_status[monitor_name][updatestatus.ERROR] = result['error']
    if 'updatedEntity' in result:
        all_monitor_status[monitor_name][updatestatus.UPDATED_JSON] = result['updatedEntity']


def main():
    parser = argparse.ArgumentParser(description='Update Synthetic Monitors')
    setup_params(parser)
    args = parser.parse_args()
    if not args.renamePrefix and not args.disable and not args.enable:
        logger.error("Missing update directive: One or more of --renamePrefix, --disable, or --enable flags must be passed")
        sys.exit(1)
    target_api_key = ensure_target_api_key(args)
    rename_prefix = ''
    disable = False
    enable = False
    if args.renamePrefix:
        rename_prefix = args.renamePrefix[0]
    if args.disable:
        disable = True
    if args.enable:
        enable = True
    targetRegion = utils.ensure_target_region(args)
    print_args(args, targetRegion)
    update_monitors(target_api_key, args.targetAccount[0], args.fromFile[0], args.timeStamp[0],
                    rename_prefix, disable, enable, targetRegion)


if __name__ == '__main__':
    main()
