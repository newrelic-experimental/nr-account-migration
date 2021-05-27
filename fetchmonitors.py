import argparse
import os
import sys
import time
import library.localstore as store
import library.monitortypes as monitortypes
import library.clients.monitorsclient as mc
import library.migrationlogger as m_logger
import library.securecredentials as securecredentials
import library.utils as utils

# fetch monitors from an account
# sourceAccount : account to fetch the monitors from
# sourceApiKey : User API Key for the account for a user with admin (or add on / custom role equivalent) access to Synthetics
# toFile : file name only for the output file
# the toFile will be written to output sub-directory
# If file exists then it will be overwritten


logger = m_logger.get_logger(os.path.basename(__file__))
headers = {}
source_api_key = ""


parser = argparse.ArgumentParser(description='Get list of all monitors')
# store API Test and Scripted browser montiors to fetch their library in the next step
script_monitors = []


def setup_params():
    parser.add_argument('--sourceAccount', nargs=1, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--insightsQueryKey', type=str, nargs=1, required=False, help='Insights Query Key to '
                                                                                      'fetch secure credentials')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='region us(default) or eu')
    parser.add_argument('--toFile', nargs=1, required=True, help='File to populate monitor names. '
                                                                 'This will be created in output directory')


def print_params():
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4])*"*"+source_api_key[-4:])
    if args.region and len(args.region) > 0:
        logger.info("region : " + args.region[0])
    else:
        logger.info("region not passed : Defaulting to " + region)
    if args.insightsQueryKey and len(args.insightsQueryKey) > 0:
        logger.info("Using insightsQueryKey to fetch secure credentials : " +
                    len(args.insightsQueryKey[0][:-4]) * "*" + args.insightsQueryKey[0][-4:])
    else:
        logger.info("Will skip fetching secure credentials as insightsQueryKey is not provided")
    logger.info("Using toFile : " + args.toFile[0])


def setup_headers(api_key):
    global source_api_key
    if args.sourceApiKey:
        source_api_key = api_key
        headers['Api-Key'] = args.sourceApiKey[0]
    else:
        source_api_key = os.environ.get('ENV_SOURCE_API_KEY')
        headers['Api-Key'] = source_api_key
    logger.debug(headers)
    validate_keys()


def validate_keys():
    if not source_api_key:
        logger.error('Error: Missing API Key. either pass as param ---sourceApiKey or \
                environment variable ENV_SOURCE_API_KEY.\n \
                e.g. export SOURCE_API_KEY="NRNA7893asdfhkh"')
        sys.exit()


def populate_secure_credentials(monitor_json, src_account, insights_key, region):
    if insights_key:
        sec_credentials_checks = securecredentials.from_insights(
            insights_key, src_account, monitor_json['definition']['name'], region)
        monitor_json.update(sec_credentials_checks)


def fetch_monitors(api_key, account_id, output_file, insights_key='', region='us'):
    all_monitors_def_json = mc.fetch_all_monitors(api_key, region)
    monitors_count = len(all_monitors_def_json)
    if monitors_count <= 0:
        logger.warn("No monitors found in account " + account_id)
        sys.exit()
    else:
        logger.info("Monitors returned %d", monitors_count)
    timestamp = time.strftime("%Y-%m%d-%H%M%S")
    storage_dir = store.create_storage_dirs(account_id, timestamp)
    monitor_names_file = store.create_output_file(output_file)
    with monitor_names_file.open('a') as monitor_names_out:
        for monitor_def_json in all_monitors_def_json:
            monitor_json = {'definition': monitor_def_json}
            monitor_name = store.sanitize(monitor_def_json['name'])
            monitor_names_out.write(monitor_name + "\n")
            if monitortypes.is_scripted(monitor_json['definition']):
                populate_secure_credentials(monitor_json, account_id, insights_key, region)
                mc.populate_script(api_key, monitor_json, monitor_json['definition']['id'])
            store.save_monitor_to_file(monitor_name, storage_dir, monitor_json)
    logger.info("Fetched %d monitors in %s", len(all_monitors_def_json), storage_dir)
    return timestamp


if __name__ == '__main__':
    start_time = time.time()
    setup_params()
    args = parser.parse_args()
    setup_headers(args.sourceApiKey[0])
    args_insights_key = ''
    if args.insightsQueryKey:
        args_insights_key = args.insightsQueryKey[0]
    region = utils.ensure_region(args)
    print_params()
    fetch_monitors(source_api_key, str(args.sourceAccount[0]), args.toFile[0], args_insights_key, )
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")
