import argparse
import json
import os
import sys
import time
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.clients.monitorsclient as mc
import library.monitortypes as monitortypes
import library.securecredentials as securecredentials
import library.status.monitorstatus as mskeys
import library.utils as utils

# migratemonitors must be used after doing a fetchmonitors
# specify the source account, timestamp that you want to migrate
# Also specify the targetAccount and targetApiKey to which you want to migrate the stored monitors

logger = migrationlogger.get_logger(os.path.basename(__file__))
headers = {}
args = None
fetch_latest = True
# The following two constants are used to create the alert policy to which the monitor check alerts are migrated
SYNTHETICS_ALERT_POLICY_NAME = 'Synthetics Check Failures'
INCIDENT_PREFERENCE_OPTIONS = {'PER_POLICY': 'PER_POLICY', 'PER_CONDITION': 'PER_CONDITION',
                               'PER_CONDITION_TARGET': 'PER_CONDITION PER_CONDITION_AND_TARGET'}

def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate Synthetic Monitors from one account to another')
    parser.add_argument('--fromFile', nargs=1, type=str, required=True, help='Path to file with monitor names')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId local Store \
                                                                        like db/<sourceAccount>/monitors .')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key, \
                                                                                ignored if useLocal is passed')
    parser.add_argument('--targetAccount', nargs=1, type=str,  required=True, help='Target accountId or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                                                                        or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--timeStamp', nargs=1, type=str, required=True, help='timeStamp to migrate')

    parser.add_argument('--useLocal', dest='useLocal', required=False, action='store_true',
                        help='By default latest monitors are fetched. Pass this argument to useLocal')
    parser.add_argument('--minionMappingFile', nargs=1, required=False, help='Map (private) minion names to alternatives using a dictionary in a json file')
    return parser


# prints args and also sets the fetch_latest flag
def print_args(args, target_api_key, src_region, tgt_region):
    global fetch_latest
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("sourceRegion : " + src_region)
    if args.sourceApiKey:
        logger.info("Using sourceApiKey(ignored if --useLocal is passed) : " +
                    len(args.sourceApiKey[0][:-4])*"*"+args.sourceApiKey[0][-4:])
    if args.useLocal:
        fetch_latest = False
        logger.info("Using useLocal : " + str(args.useLocal))
        logger.info("Switched fetch_latest to :" + str(fetch_latest))
    else:
        logger.info("Default fetch_latest :" + str(fetch_latest))
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("targetRegion : " + tgt_region)
    logger.info("Using targetApiKey : " + len(target_api_key[:-4])*"*"+target_api_key[-4:])
    logger.info("Using timeStamp : " + args.timeStamp[0])
    if args.minionMappingFile:
        logger.info("Using minionMappingFile : " + args.minionMappingFile[0])


def ensure_target_api_key():
    if args.targetApiKey:
        target_api_key = args.targetApiKey[0]
    else:
        target_api_key = os.environ.get('ENV_TARGET_API_KEY')
    if not target_api_key:
        logger.error('Error: Missing param targetApiKey or env variable ENV_TARGET_API_KEY .\n \
        e.g. export ENV_TARGET_API_KEY="NRAA7893asdfhkh" or pass as param')
        sys.exit()
    return target_api_key


def migrate(all_monitors_json, src_api_key, src_region, tgt_api_key, tgt_region, tgt_acct_id, minion_mapping_file=None):
    monitor_status = {}
    scripted_monitors = []
    for monitor_json in all_monitors_json:
        logger.debug(monitor_json)
        monitor_name = monitor_json['definition']['name']
        source_monitor_id = monitor_json['definition']['guid']
        if fetch_latest:
            result = mc.MonitorsClient.get_monitor(src_api_key, source_monitor_id, src_region)
            if result['status'] != 200:
                logger.error('Did not find monitor ' + source_monitor_id)
                logger.error(result)
                continue
            monitor_json['definition'] = result['monitor']
        if minion_mapping_file:
            # reading the data from the file
            with open(minion_mapping_file, 'r') as mapping_file:
                data = mapping_file.read()
            mappings = json.loads(data)
            for original_location in monitor_json['definition']['locations']:
                if original_location in mappings.keys():
                    revised_location = mappings[original_location]
                    monitor_json['definition']['locations'] = [location.replace(original_location, revised_location) for location in monitor_json['definition']['locations']]
        mc.MonitorsClient.post_monitor_definition(tgt_api_key, monitor_name, monitor_json, monitor_status, tgt_acct_id, tgt_region)
        if monitortypes.is_scripted(monitor_json['definition']):
            scripted_monitors.append(monitor_json)
            logger.info(monitor_status)
            if mskeys.SEC_CREDENTIALS in monitor_json:
                monitor_status[monitor_name][mskeys.SEC_CREDENTIALS] = monitor_json[mskeys.SEC_CREDENTIALS]
            if mskeys.CHECK_COUNT in monitor_json:
                monitor_status[monitor_name][mskeys.CHECK_COUNT] = monitor_json[mskeys.CHECK_COUNT]
        logger.debug(monitor_status[monitor_name])
    securecredentials.create(tgt_api_key, scripted_monitors)
    return monitor_status


def migrate_monitors(from_file, src_acct, src_region, src_api_key, time_stamp, tgt_acct_id, tgt_region, tgt_api_key, minion_mapping_file=None):
    monitor_names = store.load_names(from_file)
    logger.debug(monitor_names)
    all_monitors_json = store.load_monitors(src_acct, time_stamp, monitor_names)
    monitor_status = migrate(all_monitors_json, src_api_key, src_region, tgt_api_key, tgt_region, tgt_acct_id, minion_mapping_file)
    logger.debug(monitor_status)
    file_name = utils.file_name_from(from_file)
    status_csv = src_acct + "_" + file_name + "_" + tgt_acct_id + ".csv"
    store.save_status_csv(status_csv, monitor_status, mskeys)


def main():
    start_time = time.time()
    parser = configure_parser()
    global args
    args = parser.parse_args()
    target_api_key = ensure_target_api_key()
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    sourceRegion = utils.ensure_source_region(args)
    targetRegion = utils.ensure_target_region(args)
    print_args(args, target_api_key, sourceRegion, targetRegion)
    minion_mapping_file = args.minionMappingFile[0] if args.minionMappingFile else None
    migrate_monitors(args.fromFile[0], args.sourceAccount[0], sourceRegion, args.sourceApiKey[0], args.timeStamp[0],
                     args.targetAccount[0], targetRegion, target_api_key, minion_mapping_file)
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")


if __name__ == '__main__':
    main()
