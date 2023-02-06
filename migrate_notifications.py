import os
import argparse
import fetchnotifications as fetchnotifications
import library.clients.notificationsclient as notificationsclient
import library.localstore as store
import library.migrationlogger as m_logger
import library.utils as utils


log = m_logger.get_logger(os.path.basename(__file__))
nc = notificationsclient.NotificationsClient()


def print_args(args, src_api_key, src_region, tgt_api_key, tgt_region):
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    log.info("sourceRegion : " + src_region)
    log.info("Using targetAccount : " + str(args.targetAccount[0]))
    log.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    log.info("targetRegion : " + tgt_region)


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate Notifications')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    parser.add_argument('--destinations', dest='destinations', required=False, action='store_true', help='Migrate destinations')
    parser.add_argument('--channels', dest='channels', required=False, action='store_true', help='Migrate channels')
    return parser


def create_email_destination(destination, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating destination: {destination['name']} of type {destination['type']}")
    response = nc.create_email_destination(destination, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created destination: {destination['name']} of type {destination['type']}")


def create_webhook_destination(destination, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating destination: {destination['name']} of type {destination['type']}")
    response = nc.create_webhook_destination(destination, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created destination: {destination['name']} of type {destination['type']}")


def create_mobile_push_destination(destination, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating destination: {destination['name']} of type {destination['type']}")
    response = nc.create_mobile_push_destination(destination, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created destination: {destination['name']} of type {destination['type']}")


def create_slack_legacy_destination(destination, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating destination: {destination['name']} of type {destination['type']}")
    response = nc.create_slack_legacy_destination(destination, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created destination: {destination['name']} of type {destination['type']}")


def create_destination(destination, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating destination: {destination['name']}")
    if destination['type'] == notificationsclient.DESTINATION_TYPE_EMAIL:
        create_email_destination(destination, tgt_acct, tgt_api_key, tgt_region)
    elif destination['type'] == notificationsclient.DESTINATION_TYPE_MOBILE_PUSH:
        create_mobile_push_destination(destination, tgt_acct, tgt_api_key, tgt_region)
    elif destination['type'] == notificationsclient.DESTINATION_TYPE_SLACK_LEGACY:
        create_slack_legacy_destination(destination, tgt_acct, tgt_api_key, tgt_region)
    elif destination['type'] == notificationsclient.DESTINATION_TYPE_WEBHOOK:
        create_webhook_destination(destination, tgt_acct, tgt_api_key, tgt_region)
    else:
        log.warn(f"Unsupported destination type: {destination['type']}, for destination: {destination['name']}")


def create_email_channel(channel, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating channel: {channel['name']} of type {channel['type']}")
    nc.create_email_channel(channel, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created channel: {channel['name']} of type {channel['type']}")


def create_webhook_channel(channel, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating channel: {channel['name']} of type {channel['type']}")
    nc.create_webhook_channel(channel, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created channel: {channel['name']} of type {channel['type']}")


def create_mobile_push_channel(channel, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating channel: {channel['name']} of type {channel['type']}")
    nc.create_mobile_push_channel(channel, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created channel: {channel['name']} of type {channel['type']}")


def create_slack_legacy_channel(channel, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating channel: {channel['name']} of type {channel['type']}")
    nc.create_slack_legacy_channel(channel, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created channel: {channel['name']} of type {channel['type']}")


def create_channel(channel, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating channel: {channel['name']}")
    if channel['type'] == notificationsclient.CHANNEL_TYPE_EMAIL:
        create_email_channel(channel, tgt_acct, tgt_api_key, tgt_region)
    elif channel['type'] == notificationsclient.CHANNEL_TYPE_MOBILE_PUSH:
        create_mobile_push_channel(channel, tgt_acct, tgt_api_key, tgt_region)
    elif channel['type'] == notificationsclient.CHANNEL_TYPE_SLACK_LEGACY:
        create_slack_legacy_channel(channel, tgt_acct, tgt_api_key, tgt_region)
    elif channel['type'] == notificationsclient.CHANNEL_TYPE_WEBHOOK:
        create_webhook_channel(channel, tgt_acct, tgt_api_key, tgt_region)
    else:
        log.warn(f"Unsupported channel type: {channel['type']}, for channel: {channel['name']}")


def migrate_destinations(src_acct, src_api_key, src_region, tgt_acct, tgt_api_key, tgt_region):
    log.info('Destinations migration started.')
    destinations_by_source_id = fetchnotifications.fetch_destinations(src_api_key, src_acct, src_region)
    for destination in destinations_by_source_id.values():
        log.info(f"Destination name: {destination['name']}")
        create_destination(destination, tgt_acct, tgt_api_key, tgt_region)
    log.info('Destinations migration complete.')
    return destinations_by_source_id


def migrate_channels(src_acct, src_api_key, src_region, tgt_acct, tgt_api_key, tgt_region, destinations_by_source_id):
    log.info('Channels migration started.')
    channels_by_source_id = fetchnotifications.fetch_channels(src_api_key, src_acct, src_region)
    for channel in channels_by_source_id.values():
        log.info(f"Channel name: {channel['name']}")
        log.info(f"Mutating destination id for target account: {tgt_acct}")
        source_destination_id = channel['destinationId']
        if source_destination_id in destinations_by_source_id:
            if 'targetDestinationId' in destinations_by_source_id.get(source_destination_id):
                # Mutate channel destinationId, replacing destinationId with targetDestinationId
                channel['destinationId'] = destinations_by_source_id.get(source_destination_id)['targetDestinationId']
                log.info(f"Substituting destination id: {source_destination_id} with id: {(channel['destinationId'])}")
                create_channel(channel, tgt_acct, tgt_api_key, tgt_region)
            else:
                log.error(f"Unable to create channel name: {channel['name']}, with source channel id: {channel['id']} and type: {channel['type']}. Target destination id unavailable for source destination: {source_destination_id}")                
    log.info('Channels migration complete.')
    return channels_by_source_id


def main():
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    if not src_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    tgt_api_key = utils.ensure_target_api_key(args)
    if not tgt_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    src_region = utils.ensure_source_region(args)
    tgt_region = utils.ensure_target_region(args)
    print_args(args, src_api_key, src_region, tgt_api_key, tgt_region)
    if args.destinations:
        migrate_destinations(args.sourceAccount[0], src_api_key, src_region, args.targetAccount[0], tgt_api_key, tgt_region)
    elif args.channels:
        # TODO missing destinations_by_source_id argument!
        migrate_channels(args.sourceAccount[0], src_api_key, src_region, args.targetAccount[0], tgt_api_key, tgt_region)
    else:
        log.info("pass [--destinations | --channels] to fetch configuration")


if __name__ == '__main__':
    main()
