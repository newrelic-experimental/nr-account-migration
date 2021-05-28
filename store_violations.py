import argparse
import os
import library.localstore as store
import library.status.alertstatus as askeys
import library.migrationlogger as m_logger
import library.clients.violationsclient as vc
import library.utils as utils
import fetchchannels

# Migrates alert policy and assigned notification channels to targetAccount
# Alert Policy and Notification Channels are created only if not present in the targetAccount

log = m_logger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Store Alert Policies and channels')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--startDate', nargs=1, type=str, required=True,
                        help='startDate format 2020-08-03T19:18:00+00:00')
    parser.add_argument('--endDate', nargs=1, type=str, required=True,
                        help='endDate format 2020-08-04T19:18:00+00:00')
    parser.add_argument('--onlyOpen', dest='onlyOpen', required=False, action='store_true',
                        help='By default all violations are fetched pass --onlyOpen to fetch only open violations')
    return parser


def print_args(src_api_key, src_account, src_region, start_date, end_date, only_open):
    log.info("sourceAccount : " + src_account)
    log.info("sourceRegion  : " + src_region)
    log.info("sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    log.info("startDate : " + start_date)
    log.info("endDate : " + end_date)
    log.info("onlyOpen flag : " + str(only_open))


def store_alert_violations(src_api_key, src_account, src_region, start_date, end_date, only_open=False):
    log.info('Starting store alert violations.')
    violations = vc.get_all_alert_violations(src_api_key, start_date, end_date, only_open, src_region)
    store.save_alert_violations(src_account, violations)
    store.save_alert_violations_csv(src_account, violations)
    log.info('Finished store alert violations.')


def main():
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    if not src_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    src_region = utils.ensure_source_region(args)
    only_open = False
    if args.onlyOpen:
        only_open = True
        log.info("Using onlyOpen : " + str(args.onlyOpen))
    else:
        log.info("Using default onlyOpen :" + str(only_open))
    print_args(src_api_key, args.sourceAccount[0], src_region, args.startDate[0], args.endDate[0], only_open)
    store_alert_violations(src_api_key, args.sourceAccount[0], src_region, args.startDate[0], args.endDate[0], only_open)


if __name__ == '__main__':
    main()
