import argparse
import os
import sys
import library.localstore as store
import library.status.alertstatus as askeys
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.utils as utils
import fetchchannels

# Migrates alert policy and assigned notification channels to targetAccount
# Alert Policy and Notification Channels are created only if not present in the targetAccount

logger = m_logger.get_logger(os.path.basename(__file__))
fetch_channels = True


def setup_params():
    parser.add_argument('--fromFile', nargs=1, type=str, required=False, help='Path to file with alert policy names')
    parser.add_argument('--fromFileEntities', nargs=1, type=str, required=False, help='Path to file with entity IDs')
    parser.add_argument('--personalApiKey', nargs=1, type=str, required=True, help='Personal API Key for GraphQL client \
                                                                    alternately environment variable ENV_PERSONAL_API_KEY')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=False, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--useLocal', dest='useLocal', required=False, action='store_true',
                        help='By default channels are fetched.Pass this to use channels pre-fetched by fetchchannels')


# prints args and also sets the fetch_latest flag
def print_args(per_api_key, src_api_key, tgt_api_key):
    global fetch_channels
    if (args.fromFile):
        logger.info("Using fromFile : " + args.fromFile[0])
    if (args.fromFileEntities):
        logger.info("Using fromFileEntities : " + args.fromFileEntities[0])
    logger.info("Using personalApiKey : " + len(per_api_key[:-4])*"*"+per_api_key[-4:])
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    if args.useLocal:
        fetch_channels = False
        logger.info("Using useLocal : " + str(args.useLocal))
        logger.info("Switched fetch_channels to :" + str(fetch_channels))
    else:
        logger.info("Default fetch_channels :" + str(fetch_channels))


def type_name_key(channel):
    return channel['type'] + '-' + channel['name']


def get_channels_by_type_name(api_key):
    result = ac.get_channels(api_key)
    all_target_channels = result[askeys.CHANNELS]
    target_channels_by_type_name = {}
    for target_channel in all_target_channels:
        target_channels_by_type_name[type_name_key(target_channel)] = target_channel
    return target_channels_by_type_name


def update_notification_channels(tgt_api_key, source_policy, target_policy, loaded_src_channels,
                                 tgt_channels_by_type_name, all_alert_status):
    logger.info('Updating notification channels for ' + target_policy['name'])
    src_policy_id = str(source_policy['id'])
    if not loaded_src_channels['channels_by_policy_id']:
        logger.info('No notification channel subscriptions')
        return
    if src_policy_id in loaded_src_channels['channels_by_policy_id']:
        src_channel_ids = loaded_src_channels['channels_by_policy_id'][src_policy_id]
    src_channels = []
    for source_channel_id in src_channel_ids:
        if str(source_channel_id) in loaded_src_channels['channels_by_id']:
            src_channels.append(loaded_src_channels['channels_by_id'][str(source_channel_id)])
    target_channel_ids = []
    for src_channel in src_channels:
        src_channel_type_name = type_name_key(src_channel)
        if src_channel_type_name not in tgt_channels_by_type_name:
            result = ac.create_channel(tgt_api_key, src_channel)
            if result['status'] == 201:
                tgt_type_name = type_name_key(result['channel'])
                logger.info('Created channel : ' + tgt_type_name)
                tgt_channels_by_type_name[tgt_type_name] = result['channel']
        else:
            logger.info('Channel already existed : ' + src_channel_type_name)
        target_channel_ids.append(tgt_channels_by_type_name[src_channel_type_name]['id'])
        update_alert_status(all_alert_status, target_policy['name'], src_channel_type_name)
    result = ac.put_channel_ids(tgt_api_key, target_policy['id'], target_channel_ids)
    update_put_status(all_alert_status, result, target_policy)


def update_put_status(all_alert_status, result, target_policy):
    all_alert_status[target_policy['name']][askeys.STATUS] = result['status']
    if 'channel_ids' in result:
        all_alert_status[target_policy['name']][askeys.PUT_CHANNELS] = result['channel_ids']


def update_alert_status(all_alert_status, policy_name, src_channel_type_name):
    if askeys.CHANNELS in all_alert_status[policy_name]:
        all_alert_status[policy_name][askeys.CHANNELS] = all_alert_status[policy_name][askeys.CHANNELS] \
                                                         + ";" + src_channel_type_name
    else:
        all_alert_status[policy_name][askeys.CHANNELS] = src_channel_type_name


def migrate_alert_policies(policy_names, src_account, src_api_key, tgt_account, tgt_api_key):
    logger.info('Alert migration started.')
    all_alert_status = {}
    if fetch_channels:
        logger.info('Fetching latest channel info and policy assignment. This may take a while.....')
        loaded_src_channels = fetchchannels.get_channels_by_id_policy(src_api_key)
    else:
        logger.info('Loading pre-fetched channel and policy assignment information')
        loaded_src_channels = store.load_alert_channels(src_account)
    tgt_channels_by_type_name = get_channels_by_type_name(tgt_api_key)

    logger.info('Migrating the following policies:')
    logger.info('%s' % policy_names)

    for policy_name in policy_names:
        all_alert_status[policy_name] = {}
        result = ac.get_policy(src_api_key, policy_name)
        if not result['policyFound']:
            logger.error("Skipping as policy not found in source account " + policy_name)
            all_alert_status[policy_name][askeys.ERROR] = "Policy Not found in source account"
            continue
        src_policy = result['policy']
        result = ac.get_policy(tgt_api_key, policy_name)
        if result['status'] in [200, 304] and result['policyFound']:
            logger.info('Policy exists : ' + policy_name)
            all_alert_status[policy_name] = {askeys.POLICY_EXISTED: True}
            tgt_policy = result['policy']
        else:
            logger.info('Creating : ' + policy_name)
            all_alert_status[policy_name] = {askeys.POLICY_EXISTED: False}
            result = ac.create_alert_policy(tgt_api_key, src_policy)
            update_create_status(all_alert_status, policy_name, result)
            tgt_policy = result['policy']
        update_notification_channels(tgt_api_key, src_policy, tgt_policy, loaded_src_channels,
                                     tgt_channels_by_type_name, all_alert_status)
    logger.info('Alert migration complete.')
    return all_alert_status


def update_create_status(all_alert_status, policy_name, result):
    all_alert_status[policy_name][askeys.STATUS] = result['status']
    all_alert_status[policy_name][askeys.POLICY_CREATED] = result['entityCreated']
    if 'error' in result:
        all_alert_status[policy_name][askeys.ERROR] = result['error']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate Alert Policies and channels')
    setup_params()
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    personal_api_key = utils.ensure_personal_api_key(args)
    if not personal_api_key:
        utils.error_and_exit('personal_api_key', 'ENV_PERSONAL_API_KEY')

    fromFile = args.fromFile[0] if 'fromFile' in args else None
    fromFileEntities = args.fromFileEntities[0] if 'fromFileEntities' in args else None
    if not fromFile and not fromFileEntities:
        logger.error('Error: At least one of fromFile or fromFileEntities must be specified.')
        sys.exit()

    source_acct_id = args.sourceAccount[0]
    target_acct_id = args.targetAccount[0]

    print_args(personal_api_key, source_api_key, target_api_key)

    policy_names = utils.load_alert_policy_names(
        fromFile,
        fromFileEntities,
        source_acct_id,
        source_api_key,
        personal_api_key,
        args.useLocal
    )

    status = migrate_alert_policies(
        policy_names,
        source_acct_id,
        source_api_key,
        target_acct_id,
        target_api_key
    )

    status_file = ac.get_alert_status_file_name(
        fromFile,
        fromFileEntities,
        source_acct_id,
        target_acct_id
    )
    store.save_status_csv(status_file, status, askeys)
