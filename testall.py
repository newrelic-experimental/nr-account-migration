import os
import time

import deleteallmonitors as deleter
import fetchchannels as fetchchannels
import fetchmonitors as fetchmonitors
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
import library.migrationlogger as m_logger
import library.securecredentials as sec_credentials
import migrate_apm as mapm
import migrate_dashboards as md
import migrateconditions as mc
import migratemonitors as mm
import migratepolicies as mp

TGT_ACCT = ''
TGT_API_KEY = ''
SRC_ACCT = ''
SRC_API_KEY = ''
SRC_INSIGHTS_KEY = ''


MON_LIST_FILE = 'test-monitors.csv'
ALERTS_LIST_FILE = 'output/alerts1.csv'
SINGLE_ALERTS_FILE = 'output/alerts2.csv'
DASHBOARDS_LIST_FILE = 'output/dashboards.csv'
APP_FILE = 'output/apps_migrated.csv'
time_stamp = ''  # will be updated by fetch step
PER_API_KEY = ''
APP_NAME = ''
MONITOR_NAME = 'cb-load-home'

COND_TYPES = mc.ALL_CONDITIONS

logger = m_logger.get_logger(os.path.basename(__file__))


def cleanup():
    logger.info('Cleaning up test target account')
    logger.info('Deleting all monitors')
    deleter.delete_all_monitors(TGT_API_KEY, TGT_ACCT)
    time.sleep(1)
    logger.info('Deleting all secure credentials')
    sec_credentials.delete_all(TGT_API_KEY, TGT_ACCT)
    time.sleep(1)
    logger.info('Deleting all alert policies')
    ac.delete_all_policies(TGT_API_KEY, TGT_ACCT)
    time.sleep(1)
    logger.info('Deleting all alert channels')
    ac.delete_all_channels(TGT_API_KEY, TGT_ACCT)
    time.sleep(1)
    reset_app()
    logger.info('deleting all target dashboards')
    ec.delete_all_dashboards(TGT_API_KEY)


def reset_app():
    logger.info('Resetting labels and settings for ' + APP_NAME)
    tgt_result = ec.gql_get_matching_entity_by_name(PER_API_KEY, ec.APM_APP, APP_NAME, TGT_ACCT)
    tgt_entity = tgt_result['entity']
    ec.gql_mutate_replace_tags(PER_API_KEY, tgt_entity['guid'], [])
    ec.put_apm_settings(TGT_API_KEY, tgt_entity['applicationId'], {
        'application': {'settings': {'app_apdex_threshold': '0.5', 'end_user_apdex_threshold': '7',
                                     'enable_real_user_monitoring': 'False'}}})


def fetch():
    global time_stamp
    logger.info('Fetching')
    time_stamp = fetchmonitors.fetch_monitors(SRC_API_KEY, SRC_ACCT, MON_LIST_FILE, SRC_INSIGHTS_KEY)
    logger.info('Timestamp for fetched monitors ' + time_stamp)
    logger.info('Fetching alert channels for policies')
    fetchchannels.fetch_alert_channels(SRC_API_KEY, SRC_ACCT)


def del_all_dashboards():
    ec.delete_all_dashboards(TGT_API_KEY)


def quick_test():
    src_entity = {'name': 'noteService', 'language': 'java', 'type': 'APPLICATION'}
    tgt_entity = ec.gql_get_matching_entity(PER_API_KEY, ec.APM_APP, src_entity, TGT_ACCT)
    print(str(tgt_entity))


def migrate():
    logger.info('migrating monitors')
    mm.migrate_monitors('output/' + MON_LIST_FILE, SRC_ACCT, SRC_API_KEY, time_stamp, TGT_ACCT, TGT_API_KEY)
    mp.migrate_alert_policies(ALERTS_LIST_FILE, SRC_ACCT, SRC_API_KEY, TGT_ACCT, TGT_API_KEY)
    mc.migrate_conditions(ALERTS_LIST_FILE,  PER_API_KEY, SRC_ACCT, SRC_API_KEY, TGT_ACCT, TGT_API_KEY, COND_TYPES)
    mapm.migrate_apps(APP_FILE, SRC_ACCT, SRC_API_KEY, PER_API_KEY, TGT_ACCT, TGT_API_KEY)
    md.migrate_dashboards(DASHBOARDS_LIST_FILE, SRC_ACCT, SRC_API_KEY, TGT_ACCT, TGT_API_KEY)


def migrate_alerts():
    mc.migrate_conditions(SINGLE_ALERTS_FILE,  PER_API_KEY, SRC_ACCT, SRC_API_KEY, TGT_ACCT, TGT_API_KEY, COND_TYPES)


def mig_dashboards():
    md.migrate_dashboards(DASHBOARDS_LIST_FILE, SRC_ACCT, SRC_API_KEY, TGT_ACCT, TGT_API_KEY)


def get_secure_credentials():
    cred_checks = sec_credentials.from_insights(
        SRC_INSIGHTS_KEY, SRC_ACCT, MONITOR_NAME)
    print(str(cred_checks))


def full_test():
    cleanup()
    fetch()
    migrate()


def test_get_monitor_by_name():
    result = ec.gql_get_matching_entity_by_name(PER_API_KEY, ec.SYNTH_MONITOR, MONITOR_NAME, TGT_ACCT)
    logger.info(str(result))
    assert result['status'] == 200
    assert result['entity']['entityType'] == 'SYNTHETIC_MONITOR_ENTITY'
    assert result['entity']['monitorType'] == 'BROWSER'
    assert result['entity']['name'] == MONITOR_NAME


if __name__ == '__main__':
    migrate_alerts()
    # cleanup()
    # get_secure_credentials()
    # del_all_dashboards()
    # mig_dashboards()
    # quick_test()
    # test_get_monitor_by_name()
    # full_test()
