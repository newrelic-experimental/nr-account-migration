import argparse
import os
import sys
import time
import library.localstore as store
import library.migrationlogger as migrationlogger
import library.clients.alertsclient as ac
import library.utils as utils


logger = migrationlogger.get_logger(os.path.basename(__file__))
source_api_key = ""


def configure_parser():
    parser = argparse.ArgumentParser(description='Fetch and store channels by alert policy id')
    parser.add_argument('--sourceAccount', type=str, nargs=1, required=True, help='Source accountId to store the alerts')
    parser.add_argument('--sourceApiKey', type=str, nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')
    parser.add_argument('--region', type=str, nargs=1, required=False, help='region us(default) or eu')
    return parser


def print_params(args, source_api_key, region):
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4]) * "*" + source_api_key[-4:])
    if args.region and len(args.region) > 0:
        logger.info("region : " + args.region[0])
    else:
        logger.info("region not passed : Defaulting to " + region)


# fetches all channels restructures into a dictionary as below
# channels_by_id: {
#        channel_id: {}
# }
# channel_by_policy_id {
#        alert_policy_id: [channel_id]
# }
# links": { "policy_ids": [] }
def get_channels_by_id_policy(api_key, region):
    src_channels = ac.get_channels(api_key, region)
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


def fetch_alert_channels(api_key, account_id, region):
    all_channels = get_channels_by_id_policy(api_key, region)
    store.save_alert_channels(account_id, all_channels)


def main():
    start_time = time.time()
    parser = configure_parser()
    args = parser.parse_args()
    args_api_key = ''
    if args.sourceApiKey:
        args_api_key = args.sourceApiKey[0]
    region = utils.ensure_region(args)
    print_params(args, source_api_key, region)
    fetch_alert_channels(args_api_key, args.sourceAccount[0], region)
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")


if __name__ == '__main__':
    main()
