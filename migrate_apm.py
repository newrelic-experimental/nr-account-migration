import argparse
import os
import library.migrationlogger as m_logger
import library.utils as utils
import library.localstore as store
import library.clients.entityclient as ec
import library.status.appstatus as appkeys

logger = m_logger.get_logger(os.path.basename(__file__))
MIGRATE_SETTINGS = 'settings'
DEFAULT_MIGRATE_LIST = (MIGRATE_SETTINGS)
# api_key: { appName: srcEntity }
app_src_entities = {}
app_names = []


def setup_params(parser):
    parser.add_argument('--fromFile', nargs=1, type=str, required=True, help='Path to file with monitor names')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId local Store \
                                                                        like db/<sourceAccount>/monitors .')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key')
    parser.add_argument('--targetAccount', nargs=1, type=str,  required=True, help='Target accountId or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--settings', dest='settings', required=False, action='store_true',
                        help='Pass --settings to migrate settings for apdex thresholds and real end user monitoring')

def print_args(src_api_key, tgt_api_key):
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4]) * "*" + src_api_key[-4:])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    if args.settings:
        logger.info("Migrating APM Settings")
    

def get_entity_by_name(api_key, app_name):
    result = ec.get_apm_entity_by_name(api_key, app_name)
    if not result['entityFound']:
        logger.warning('Could not locate source application ' + app_name)
        return None
    return result['entity']


def get_src_entity(api_key, app_name):
    global app_src_entities
    if api_key in app_src_entities and app_name in app_src_entities[api_key]:
        return app_src_entities[api_key][app_name]
    src_entity = get_entity_by_name(api_key, app_name)
    if api_key in app_src_entities:
        app_src_entities[api_key][app_name] = src_entity
    else:
        app_src_entities[api_key] = {app_name: src_entity}
    return src_entity


# from_file contains list of app_names whose settings need to be migrated
def migrate_settings(from_file, src_api_key, tgt_api_key, all_apps_status):
    global app_names
    if not app_names:
        app_names = store.load_names(from_file)
    for app_name in app_names:
        src_entity = get_src_entity(src_api_key, app_name)
        if src_entity is None:
            logger.warn('Could not find src entity skipping ' + app_name)
            continue
        tgt_entity = get_entity_by_name(tgt_api_key, app_name)
        if tgt_entity is None:
            logger.warn('Could not find target entity skipping ' + app_name)
            continue
        src_settings = {'settings': src_entity['settings']}
        logger.info('Updating settings for ' + app_name)
        result = ec.put_apm_settings(tgt_api_key, str(tgt_entity['id']), {'application': src_settings})
        logger.info('Updated settings results ' + app_name + str(result))
        update_settings_status(all_apps_status, app_name, result)


def update_settings_status(all_apps_status, app_name, result):
    if app_name not in all_apps_status:
        all_apps_status[app_name] = {appkeys.SETTINGS_STATUS: result['status']}
    else:
        all_apps_status[app_name][appkeys.SETTINGS_STATUS] = result['status']
    all_apps_status[app_name][appkeys.APDEX_T] = result['application']['settings']['app_apdex_threshold']
    all_apps_status[app_name][appkeys.ENDUSER_APDEX_T] = result['application']['settings']['end_user_apdex_threshold']
    all_apps_status[app_name][appkeys.ENABLE_RUM] = result['application']['settings']['enable_real_user_monitoring']


def migrate_apps(from_file, src_acct, src_api_key, 
                 tgt_acct, tgt_api_key, migrate_list=DEFAULT_MIGRATE_LIST):
    all_apps_status = {}
    if MIGRATE_SETTINGS in migrate_list:
        migrate_settings(from_file, src_api_key, tgt_api_key, all_apps_status)
    file_name = utils.file_name_from(from_file)
    status_csv = src_acct + "_" + file_name + "_migrate_apm_" + tgt_acct + ".csv"
    store.save_status_csv(status_csv, all_apps_status, appkeys)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate APM settings for list of apps from one account to another')
    setup_params(parser)
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('sourceApiKey', 'ENV_SOURCE_API_KEY')
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('targetApiKey', 'ENV_TARGET_API_KEY')
    if not args.settings and not args.labels:
        logger.error("One or both of --labels or --settings must be passed")
    print_args(source_api_key, target_api_key)
    mig_list = []
    if args.settings:
        mig_list.append(MIGRATE_SETTINGS)
    migrate_apps(args.fromFile[0], args.sourceAccount[0], source_api_key, 
                 args.targetAccount[0], target_api_key, mig_list)
