import argparse
import configparser
import os
import sys

from typing import List

import library.localstore as store
import library.status.alertstatus as askeys
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.utils as utils
import fetchchannels

"""Policy Migration Routines

Migrate alert policy and assigned notification channels to targetAccount.

Alert Policy and Notification Channels are created only if not present in
the targetAccount.
"""

logger = m_logger.get_logger(os.path.basename(__file__))
fetch_channels = True


def create_argument_parser():
    parser = argparse.ArgumentParser(
        description='Migrate Alert Policies and channels'
    )
    return configure_parser(parser)


def configure_parser(
    parser: argparse.ArgumentParser,
    is_standalone: bool = True
):
    parser.add_argument(
        '--fromFile',
        '--policy_file',
        nargs=1,
        type=str,
        required=False,
        help='Path to file with alert policy names',
        dest='policy_file'
    )
    parser.add_argument(
        '--fromFileEntities',
        '--entity_file',
        nargs=1,
        type=str,
        required=False,
        help='Path to file with entity IDs',
        dest='entity_file'
    )
    parser.add_argument(
        '--sourceAccount',
        '--source_account_id',
        nargs=1,
        type=int, 
        required=is_standalone,
        help='Source accountId',
        dest='source_account_id'
    )
    parser.add_argument(
        '--sourceRegion',
        '--source_region',
        nargs=1,
        type=str,
        required=False,
        help='Source Account Region us(default) or eu',
        dest='source_region'
    )
    parser.add_argument(
        '--sourceApiKey',
        '--source_api_key',
        nargs=1,
        type=str,
        required=False,
        help='Source account API Key or set environment variable ENV_SOURCE_API_KEY',
        dest='source_api_key'
    )
    parser.add_argument(
        '--targetAccount',
        '--target_account_id',
        nargs=1,
        type=int, 
        required=is_standalone,
        help='Target accountId',
        dest='target_account_id'
    )
    parser.add_argument(
        '--targetRegion',
        '--target_region',
        nargs=1,
        type=str,
        required=is_standalone,
        help='Target Account Region us(default) or eu',
        dest='target_region'
    )
    parser.add_argument(
        '--targetApiKey',
        '--target_api_key',
        nargs=1,
        type=str,
        required=False,
        help='Target API Key, or set environment variable ENV_TARGET_API_KEY',
        dest='target_api_key'
    )
    parser.add_argument(
        '--useLocal',
        '--use_local',
        required=False,
        action='store_true',
        help='By default channels are fetched.Pass this to use channels pre-fetched by fetchchannels',
        dest='use_local'
    )
    return parser


# prints args and also sets the fetch_latest flag
def print_args(args, src_api_key, src_region, tgt_api_key, tgt_region):
    global fetch_channels
    if (args.policy_file):
        logger.info("Using fromFile : " + args.policy_file[0])
    if (args.entity_file):
        logger.info("Using fromFileEntities : " + args.entity_file[0])
    logger.info("Using sourceAccount : " + str(args.source_account_id[0]))
    logger.info("sourceRegion : " + src_region)
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    logger.info("Using targetAccount : " + str(args.target_account_id[0]))
    logger.info("targetRegion : " + tgt_region)
    logger.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    if args.use_local:
        fetch_channels = False
        logger.info("Using useLocal : " + str(args.use_local))
        logger.info("Switched fetch_channels to :" + str(fetch_channels))
    else:
        logger.info("Default fetch_channels :" + str(fetch_channels))


def type_name_key(channel):
    return channel['type'] + '-' + channel['name']


def get_channels_by_type_name(api_key, region):
    result = ac.get_channels(api_key, region)
    all_target_channels = result[askeys.CHANNELS]
    target_channels_by_type_name = {}
    for target_channel in all_target_channels:
        target_channels_by_type_name[type_name_key(target_channel)] = target_channel
    return target_channels_by_type_name


def update_notification_channels(tgt_api_key, tgt_region, source_policy, target_policy, loaded_src_channels,
                                 tgt_channels_by_type_name, all_alert_status):
    logger.info('Updating notification channels for ' + target_policy['name'])
    src_policy_id = str(source_policy['id'])
    if not loaded_src_channels['channels_by_policy_id']:
        logger.info('No notification channel subscriptions')
        return
    src_channel_ids = []
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
            logger.info(src_channel)
            result = ac.create_channel(tgt_api_key, src_channel, tgt_region)
            if result['status'] == 201:
                tgt_type_name = type_name_key(result['channel'])
                logger.info('Created channel : ' + tgt_type_name)
                tgt_channels_by_type_name[tgt_type_name] = result['channel']
            else:
                logger.error(result)  # getting errors for channel of type user
        else:
            logger.info('Channel already existed : ' + src_channel_type_name)
        if src_channel_type_name in tgt_channels_by_type_name:
            target_channel_ids.append(tgt_channels_by_type_name[src_channel_type_name]['id'])
            update_alert_status(all_alert_status, target_policy['name'], src_channel_type_name)
    result = ac.put_channel_ids(tgt_api_key, target_policy['id'], target_channel_ids, tgt_region)
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


def migrate_alert_policies(policy_names: List[str],
                           src_account: int, src_api_key: str, src_region: str,
                           tgt_account: int, tgt_api_key: str, tgt_region: str):
    logger.info('Alert migration started.')
    all_alert_status = {}
    if fetch_channels:
        logger.info('Fetching latest channel info and policy assignment. This may take a while.....')
        loaded_src_channels = fetchchannels.get_channels_by_id_policy(src_api_key, src_region)
    else:
        logger.info('Loading pre-fetched channel and policy assignment information')
        loaded_src_channels = store.load_alert_channels(src_account)
    tgt_channels_by_type_name = get_channels_by_type_name(tgt_api_key, tgt_region)
    logger.info('Migrating the following policies:')
    logger.info('%s' % policy_names)
    for policy_name in policy_names:
        all_alert_status[policy_name] = {}
        result = ac.get_policy(src_api_key, policy_name, src_region)
        if not result['policyFound']:
            logger.error("Skipping as policy not found in source account " + policy_name)
            all_alert_status[policy_name][askeys.ERROR] = "Policy Not found in source account"
            continue
        src_policy = result['policy']
        result = ac.get_policy(tgt_api_key, policy_name, tgt_region)
        if result['status'] in [200, 304] and result['policyFound']:
            logger.info('Policy exists : ' + policy_name)
            all_alert_status[policy_name] = {askeys.POLICY_EXISTED: True}
            tgt_policy = result['policy']
        else:
            logger.info('Creating : ' + policy_name)
            all_alert_status[policy_name] = {askeys.POLICY_EXISTED: False}
            result = ac.create_alert_policy(tgt_api_key, src_policy, tgt_region)
            update_create_status(all_alert_status, policy_name, result)
            tgt_policy = result['policy']
        # update_notification_channels(tgt_api_key, tgt_region, src_policy, tgt_policy, loaded_src_channels,
        #                              tgt_channels_by_type_name, all_alert_status)
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
    source_region: str,
    target_acct_id: int,
    target_region: str,
    source_api_key: str,
    target_api_key: str,
    use_local: bool = False
):
    policy_names = utils.load_alert_policy_names(
        policy_file_path,
        entity_file_path,
        source_acct_id,
        source_region,
        source_api_key,
        use_local
    )

    status = migrate_alert_policies(
        policy_names,
        source_acct_id,
        source_api_key,
        source_region,
        target_acct_id,
        target_api_key,
        target_region
    )

    status_file = ac.get_alert_status_file_name(
        policy_file_path,
        entity_file_path,
        source_acct_id,
        target_acct_id,
        '_policies'
    )
    store.save_status_csv(status_file, status, askeys)

    return status_file


class MigratePoliciesCommand:
    def configure_parser(self, migrate_subparsers, global_options_parser):
        # Create the parser for the "policies" command
        policies_parser = migrate_subparsers.add_parser(
            'policies',
            help='policies help',
            parents=[global_options_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        configure_parser(policies_parser, False)
        policies_parser.set_defaults(func=self.run)

    def run(self, config: configparser.ConfigParser, args: argparse.Namespace):
        logger.info('Starting alert policy migration...')

        base_config = utils.process_base_config(
            config,
            'migrate.policies',
            args
        )

        policy_file_path = config.get(
            'migrate.policies',
            'policy_file',
            fallback=None
        )
        if not policy_file_path:
            if args.policy_file:
                policy_file_path = args.policy_file[0]

        entity_file_path = config.get(
            'migrate.policies',
            'entity_file',
            fallback=None
        )
        if not entity_file_path:
            if args.entity_file:
                entity_file_path = args.entity_file[0]

        if not policy_file_path and not entity_file_path:
            utils.error_message_and_exit(
                'Either a policy file or entity file must be specified.'
            )

        use_local = config.getboolean(
            'migrate.conditions',
            'use_local',
            fallback=args.use_local
        )

        migrate(
            policy_file_path,
            entity_file_path,
            base_config['source_account_id'],
            base_config['source_region'],
            base_config['target_account_id'],
            base_config['target_region'],
            base_config['source_api_key'],
            base_config['target_api_key'],
            use_local
        )
        logger.info('Completed alert policy migration.')


def main():
    parser = create_argument_parser()
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    policy_file = args.policy_file[0] if args.policy_file else None
    entity_file = args.entity_file[0] if args.entity_file else None
    if not policy_file and not entity_file:
        logger.error('Either a policy file or entity file must be specified.')
        sys.exit()
    sourceRegion = utils.ensure_source_region(args)
    targetRegion = utils.ensure_target_region(args)
    print_args(args, source_api_key, sourceRegion, target_api_key, targetRegion)
    migrate(
        policy_file,
        entity_file,
        args.source_account_id[0],
        sourceRegion,
        args.target_account_id[0],
        targetRegion,
        source_api_key,
        target_api_key,
        args.use_local
    )


if __name__ == '__main__':
    main()
