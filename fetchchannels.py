import argparse
import os
import sys
import time
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.clients.alertsclient as ac


logger = migrationlogger.get_logger(os.path.basename(__file__))
source_api_key = ""
parser = argparse.ArgumentParser(description='Fetch and store channels by alert policy id')


def setup_params():
    parser.add_argument('--sourceAccount', type=str, nargs=1, required=True, help='Source accountId to store the alerts')
    parser.add_argument('--sourceApiKey', type=str, nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')


def print_params():
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4]) * "*" + source_api_key[-4:])


def setup_headers(api_key):
    global source_api_key
    if args.sourceApiKey:
        source_api_key = api_key
    else:
        source_api_key = os.environ.get('ENV_SOURCE_API_KEY')
    validate_keys()


def validate_keys():
    if not source_api_key:
        logger.error('Error: Missing API Key. either pass as param ---sourceApiKey or \
                environment variable ENV_SOURCE_API_KEY.\n \
                e.g. export SOURCE_API_KEY="NRNA7893asdfhkh"')
        sys.exit()


# fetches all channels restructures into a dictionary as below
# channels_by_id: {
#        channel_id: {}
# }
# channel_by_policy_id {
#        alert_policy_id: [channel_id]
# }
# links": { "policy_ids": [] }
def get_channels_by_id_policy(api_key):
    src_channels = ac.get_channels(api_key)
    channels = {"channels_by_id": {}, "channels_by_policy_id": {}}
    for channel in src_channels[ac.CHANNELS]:
        channel_id = str(channel['id'])
        channels['channels_by_id'][channel_id] = channel
        for policy_id in channel['links']['policy_ids']:
            policy_id_str = str(policy_id)
            if policy_id_str not in channels['channels_by_policy_id']:
                channels['channels_by_policy_id'][policy_id_str] = [channel_id]
            else:
                channels['channels_by_policy_id'][policy_id_str].append(channel_id)
    return channels


def fetch_alert_channels(api_key, account_id):
    all_channels = get_channels_by_id_policy(api_key)
    store.save_alert_channels(account_id, all_channels)


if __name__ == '__main__':
    start_time = time.time()
    setup_params()
    args = parser.parse_args()
    args_api_key = ''
    if args.sourceApiKey:
        args_api_key = args.sourceApiKey[0]
    setup_headers(args_api_key)
    print_params()
    fetch_alert_channels(args_api_key, args.sourceAccount[0])
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")