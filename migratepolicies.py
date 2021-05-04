import argparse
import configparser
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

def create_argument_parser():
    parser = argparse.ArgumentParser(description='Migrate Alert Policies and channels')
    parser.add_argument('--fromFile', nargs=1, type=str, required=False, help='Path to file with alert policy names')
    parser.add_argument('--fromFileEntities', nargs=1, type=str, required=False, help='Path to file with entity IDs')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=False, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=False, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--useLocal', dest='useLocal', required=False, action='store_true',
                        help='By default channels are fetched.Pass this to use channels pre-fetched by fetchchannels')
    return parser


# prints args and also sets the fetch_latest flag
def print_args(src_api_key, tgt_api_key):
    global fetch_channels
    if (args.fromFile):
        logger.info("Using fromFile : " + args.fromFile[0])
    if (args.fromFileEntities):
        logger.info("Using fromFileEntities : " + args.fromFileEntities[0])
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

def migrate(
    policy_file_path: str,
    entity_file_path: str,
    source_acct_id: int,
    target_acct_id: int,
    source_api_key: str,
    target_api_key: str,
    use_local: bool = False
):
    policy_names = utils.load_alert_policy_names(
        policy_file_path,
        entity_file_path,
        source_acct_id,
        source_api_key,
        use_local
    )

    status = migrate_alert_policies(
        policy_names,
        source_acct_id,
        source_api_key,
        target_acct_id,
        target_api_key
    )

    status_file = ac.get_alert_status_file_name(
        policy_file_path,
        entity_file_path,
        source_acct_id,
        target_acct_id
    )
    store.save_status_csv(status_file, status, askeys)

    return status_file

class MigratePoliciesCommand:
    def configure_parser(self, migrate_subparsers, global_options_parser):
        # Create the parser for the "policies" command
        policies_parser = migrate_subparsers.add_parser('policies', help='policies help', parents=[global_options_parser])
        policies_parser.add_argument(
            '--policy_file',
            nargs=1,
            type=str,
            required=False,
            help='Path to file with alert policy names'
        )
        policies_parser.add_argument(
            '--entity_file',
            nargs=1,
            type=str,
            required=False,
            help='Path to file with entity names and IDs'
        )
        policies_parser.add_argument(
            '--use_local',
            dest='use_local',
            required=False,
            action='store_true',
            help='By default the policy to entity map is fetched. Pass this to use the policy to entity map pre-fetched by store_policy_entity_map.'
        )
        policies_parser.set_defaults(func=self.run)

    def run(self, config: configparser.ConfigParser, args: argparse.Namespace):
        logger.info('Starting alert policy migration...')

        base_config = utils.process_base_config(config, 'migrate.policies')

        policy_file_path = config.get(
            'migrate.conditions',
            'policy_file',
            fallback = args.policy_file
        )        
        entity_file_path = config.get(
            'migrate.conditions',
            'entity_file',
            fallback = args.entity_file
        )
        if not policy_file_path and not entity_file_path:
            utils.error_message_and_exit(
                'Error: Either a policy file or entity file must be specified.'
            )

        use_local = config.getboolean(
            'migrate.conditions',
            'use_local',
            fallback = args.use_local
        )

        migrate(
            policy_file_path,
            entity_file_path,
            base_config['source_account_id'],
            base_config['target_account_id'],
            base_config['source_api_key'],
            base_config['target_api_key'],
            use_local
        )

        logger.info('Completed alert policy migration.')

if __name__ == '__main__':
    parser = create_argument_parser()

    args = parser.parse_args()

    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')

    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')

    fromFile = args.fromFile[0] if 'fromFile' in args else None
    fromFileEntities = args.fromFileEntities[0] if 'fromFileEntities' in args else None
    if not fromFile and not fromFileEntities:
        logger.error('Error: At least one of fromFile or fromFileEntities must be specified.')
        sys.exit()

    print_args(source_api_key, target_api_key)

    migrate(
        fromFile,
        fromFileEntities,
        args.sourceAccount[0],
        args.targetAccount[0],
        source_api_key,
        target_api_key,
        args.useLocal
    )
