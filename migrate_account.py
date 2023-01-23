import os
import time

import deleteallmonitors as deleter
import fetchchannels as fetchchannels
import fetchentities as fetchentities
import fetchmonitors as fetchmonitors
import fetchnotifications as fetchnotifications
import fetchworkflows as fetchworkflows
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
import library.migrationlogger as m_logger
import library.securecredentials as sec_credentials
import library.utils as utils
import migrate_apm as mapm
import migrate_dashboards as md
import migrateconditions as mc
import migratemonitors as mm
import migratepolicies as mp
import migratetags as mt
import store_policies as store_policies

SRC_ACCT = '1234567'
SRC_API_KEY = 'NRAK-1234...'
SRC_REGION = 'us'
SRC_INSIGHTS_KEY = 'NRIQ-2345...'
TGT_ACCT = '9876543'
TGT_API_KEY = 'NRAK-9876...'
TGT_REGION = 'eu'

SRC_MON_LIST_FILE = '{}_monitors.csv'.format(SRC_ACCT)
TGT_MON_LIST_FILE = '{}_monitors.csv'.format(TGT_ACCT)
POLICY_NAME_FILE = 'output/{}_policies.csv'.format(SRC_ACCT)
ENTITY_NAME_FILE = None
USE_LOCAL = False
MATCH_SOURCE_CONDITION_STATE = True  # Match alert condition enabled/disabled state from the source account in the target account. By default, all copied alert conditions are disabled in the target account.
DASHBOARDS_LIST_FILE = 'output/{}_dashboards.csv'.format(SRC_ACCT)
APP_FILE = 'output/{}_apm.csv'.format(SRC_ACCT)
src_mon_time_stamp = ''  # will be updated by fetch step
ACCOUNT_MAPPING_FILE = 'account_mapping.json'
MINION_MAPPING_FILE = 'minion_mapping.json'
COND_TYPES = mc.ALL_CONDITIONS

logger = m_logger.get_logger(os.path.basename(__file__))


def cleanup():
    logger.info('Cleaning up test target account')
    logger.info('Deleting all monitors')
    deleter.delete_all_monitors(TGT_API_KEY, TGT_ACCT, TGT_REGION)
    time.sleep(1)
    logger.info('Deleting all secure credentials')
    sec_credentials.delete_all(TGT_API_KEY, TGT_ACCT, TGT_REGION)
    time.sleep(1)
    logger.info('Deleting all alert policies')
    ac.delete_all_policies(TGT_API_KEY, TGT_ACCT, TGT_REGION)
    time.sleep(1)
    logger.info('Deleting all alert channels')
    ac.delete_all_channels(TGT_API_KEY, TGT_ACCT, TGT_REGION)
    time.sleep(1)
    # reset_app()
    logger.info('deleting all target dashboards')
    ec.delete_all_dashboards(TGT_API_KEY, TGT_ACCT, TGT_REGION)


def fetch():
    global src_mon_time_stamp
    logger.info('Fetching')
    src_mon_time_stamp = fetchmonitors.fetch_monitors(SRC_API_KEY, SRC_ACCT, SRC_MON_LIST_FILE, SRC_INSIGHTS_KEY, SRC_REGION)
    logger.info(f'Timestamp for fetched monitors: {src_mon_time_stamp}')
    logger.info('Fetching alert channels for policies')
    store_policies.store_alert_policies(SRC_ACCT, SRC_API_KEY, SRC_REGION)
    fetchchannels.fetch_alert_channels(SRC_API_KEY, SRC_ACCT, SRC_REGION)
    fetchentities.fetch_entities(SRC_ACCT, SRC_API_KEY, [ec.DASHBOARD], '{}_dashboards.csv'.format(SRC_ACCT), tag_name=None, tag_value=None, src_region=SRC_REGION, assessment=None)
    fetchentities.fetch_entities(SRC_ACCT, SRC_API_KEY, [ec.APM_APP], '{}_apm.csv'.format(SRC_ACCT), tag_name=None, tag_value=None, src_region=SRC_REGION, assessment=None)


def migrate_step1():
    logger.info('migrating monitors')
    mm.migrate_monitors('output/' + SRC_MON_LIST_FILE, SRC_ACCT, SRC_REGION, SRC_API_KEY, src_mon_time_stamp, TGT_ACCT, TGT_REGION, TGT_API_KEY, MINION_MAPPING_FILE)
    # Migrate Synthetic monitor entity tags
    mt.migrate_tags('output/' + SRC_MON_LIST_FILE, SRC_ACCT, SRC_REGION, SRC_API_KEY, TGT_ACCT, TGT_REGION, TGT_API_KEY, [ec.SYNTH_MONITOR])
    policy_names = utils.load_alert_policy_names(
        POLICY_NAME_FILE,
        ENTITY_NAME_FILE,
        SRC_ACCT,
        SRC_REGION,
        SRC_API_KEY,
        USE_LOCAL
    )
    mp.migrate_alert_policies(policy_names, SRC_ACCT, SRC_API_KEY, SRC_REGION, TGT_ACCT, TGT_API_KEY, TGT_REGION)
    mc.migrate_conditions(policy_names, SRC_ACCT, SRC_REGION, SRC_API_KEY, TGT_ACCT, TGT_REGION, TGT_API_KEY, COND_TYPES, MATCH_SOURCE_CONDITION_STATE)


def migrate_step2():
    # Migrate APM app_apdex_threshold, end_user_apdex_threshold, and enable_real_user_monitoring settings
    mapm.migrate_apps(APP_FILE, SRC_ACCT, SRC_API_KEY, SRC_REGION, TGT_ACCT, TGT_API_KEY, TGT_REGION)
    # Migrate dashboards
    md.migrate_dashboards(DASHBOARDS_LIST_FILE, int(SRC_ACCT), SRC_API_KEY, SRC_REGION, int(TGT_ACCT), TGT_API_KEY, TGT_REGION, ACCOUNT_MAPPING_FILE)
    # Migrate APM entity tags
    mt.migrate_tags(APP_FILE, SRC_ACCT, SRC_REGION, SRC_API_KEY, TGT_ACCT, TGT_REGION, TGT_API_KEY, [ec.APM_APP])


if __name__ == '__main__':
    # cleanup()
    fetch()
    migrate_step1()
    # Redirect apps, then
    # migrate_step2()
