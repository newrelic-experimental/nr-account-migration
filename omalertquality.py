import os
import json
import argparse
import library.utils as utils
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.localstore as store

log = m_logger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Alert Quality Management Webhook operations')
    parser.add_argument('--targetAccount', nargs=1, type=str, required=True, help='Account ID')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='User API Key')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--createChannel', type=str, nargs=1, required=False,
                        help='Pass channel name to create AQM Webhook Notification Channel')
    parser.add_argument('--insertKey', type=str, nargs=1, required=False, help='Insights Insert API Key')
    parser.add_argument('--addChannel', type=str, nargs=1, required=False, help='Add this Channel name to policies '
                                                                                'listed in policyFile')
    parser.add_argument('--policyFile', type=str, nargs=1, required=False, help='File containing alert policy names. '
                                                                                'One per line. This can be generated '
                                                                                'using store_policies')
    return parser


def prepare_aqm_webhook_channel(account_id, insert_api_key, channel_name):
    webhook_channel = store.load_json_from_file('library/template', 'aqmwebhook.json')
    webhook_channel['name'] = channel_name
    webhook_channel['configuration']['headers']['X-Insert-Key'] = insert_api_key
    base_url = "https://insights-collector.newrelic.com/v1/accounts/" + str(account_id) + "/events"
    webhook_channel['configuration']['base_url'] = base_url
    return webhook_channel


def create_aqm_webhook(account_id, user_api_key, insert_api_key, channel_name, region):
    aqm_channel = prepare_aqm_webhook_channel(account_id, insert_api_key, channel_name)
    result = ac.create_channel(user_api_key, aqm_channel, region)
    if 'errors' in result:
        log.error(json.dumps(result))
    else:
        log.info(json.dumps(result))


def add_channel_to_policies(account_id, user_api_key, channel_name, policy_file, region):
    log.info("Adding channel " + channel_name + " to policies in " + policy_file)
    all_channels = ac.get_channels(user_api_key, region)
    log.info(json.dumps(all_channels))
    channel_id = -1
    for channel in all_channels['channels']:
        if channel['name'] == channel_name:
            channel_id = channel['id']
    if channel_id == -1:
        utils.error_message_and_exit("Notification channel not found " + channel_name)
    policy_names = store.load_names(policy_file)
    for policy_name in policy_names:
        result = ac.get_policy(user_api_key, policy_name, region)
        if not result['policyFound']:
            log.warn("Did not find policy skipping " + policy_name)
        log.info("Found Policy adding channel to " + policy_name)
        ac.put_channel_ids(user_api_key, result['policy']['id'], [channel_id], region)


def main():
    parser = configure_parser()
    args = parser.parse_args()
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    region = utils.ensure_target_region(args)
    if args.createChannel:
        if not args.insertKey:
            utils.error_message_and_exit("insertKey must be passed or creating channel")
        create_aqm_webhook(args.targetAccount[0], target_api_key, args.insertKey[0], args.createChannel[0], region)
    if args.addChannel:
        if not args.policyFile:
            utils.error_message_and_exit("policyFile not found. Pass policyFile listing policies to which channel "
                                         "should be added")
        add_channel_to_policies(args.targetAccount[0], target_api_key, args.addChannel[0], args.policyFile[0], region)


if __name__ == '__main__':
    main()
