import argparse
import os
import library.localstore as store
import library.status.alertstatus as askeys
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.utils as utils
import fetchchannels

# Migrates alert policy and assigned notification channels to targetAccount
# Alert Policy and Notification Channels are created only if not present in the targetAccount

log = m_logger.get_logger(os.path.basename(__file__))


def setup_params():
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')


def print_args(src_api_key, tgt_api_key):
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])


def store_alert_policies(src_account, src_api_key):
    log.info('Starting store alert policies.')
    policies = ac.get_all_alert_policies(src_api_key)
    store.save_alert_policies(src_account, policies)
    log.info('Finished store alert policies.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Store Alert Policies and channels')
    setup_params()
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    store_alert_policies(args.sourceAccount[0], source_api_key)
