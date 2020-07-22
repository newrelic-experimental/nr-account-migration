import argparse
import os
import library.migrationlogger as m_logger
import library.utils as utils
import library.localstore as store
import library.clients.entityclient as ec
import library.status.appstatus as appkeys

logger = m_logger.get_logger(os.path.basename(__file__))
MIGRATE_LABELS = 'labels'
MIGRATE_SETTINGS = 'settings'
DEFAULT_MIGRATE_LIST = (MIGRATE_LABELS, MIGRATE_SETTINGS)
# api_key: { appName: srcEntity }
app_src_entities = {}
app_names = []


def setup_params(parser):
    parser.add_argument('--fromFile', nargs=1, type=str, required=True, help='Path to file with monitor names')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId local Store \
                                                                        like db/<sourceAccount>/monitors .')
    parser.add_argument('--personalApiKey', nargs=1, type=str, required=True, help='Personal API Key')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key')
    parser.add_argument('--targetAccount', nargs=1, type=str,  required=True, help='Target accountId or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--settings', dest='settings', required=False, action='store_true',
                        help='Pass --settings to migrate settings for apdex thresholds and real end user monitoring')
    parser.add_argument('--labels', dest='labels', required=False, action='store_true',
                        help='Pass --labels to migrate labels from a source account app to target account')


def print_args(src_api_key, tgt_api_key, per_api_key):
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4]) * "*" + src_api_key[-4:])
    logger.info("Using personalApiKey : " + len(per_api_key[:-4]) * "*" + per_api_key[-4:])
    logger.info("Using targetAccount : " + str(args.targetAccount[0]))
    logger.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    if args.settings:
        logger.info("Migrating APM Settings")
    if args.labels:
        logger.info("Migrating APM Labels")


def update_labels_by_app(labels_by_app, app_id, app_labels):
    for app_label in app_labels:
        if app_label in labels_by_app:
            labels_by_app[app_label].append(app_id)
        else:
            labels_by_app[app_label] = [app_id]


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


def migrate_labels(from_file, src_acct, src_api_key, per_api_key, tgt_acct, all_apps_status):
    logger.info('Labels migration started.')
    global app_names
    app_names = store.load_names(from_file)
    apm_labels = store.load_apm_labels(src_acct)
    # tgt_guid { labels: [], entity: {} }
    tgt_guid_entity_labels = {}
    for app_name in app_names:
        src_entity = get_src_entity(src_api_key, app_name)
        if src_entity is None:
            continue
        tgt_result = ec.gql_get_matching_entity_by_name(per_api_key, ec.APM_APP, src_entity['name'], tgt_acct)
        if tgt_result['entityFound']:
            tgt_entity = tgt_result['entity']
            tgt_guid = tgt_entity['guid']
            src_app_id = str(src_entity['id'])
            if src_app_id in apm_labels:
                tgt_guid_entity_labels[tgt_guid] = {'labels': apm_labels[src_app_id], 'entity': tgt_entity}
            else:
                logger.warn('Labels not found for ' + app_name + ' in ' + store.apm_labels_location(src_acct))
                logger.warn('Make sure you have run fetchlabels for this account and this app has labels ')
        else:
            logger.warn('App not found for one of the accounts src:' + str(src_entity) + " tgt:" + str(tgt_result))
    for tgt_guid in tgt_guid_entity_labels:
        tgt_app_name = tgt_guid_entity_labels[tgt_guid]['entity']['name']
        tgt_app_labels = tgt_guid_entity_labels[tgt_guid]['labels']
        result = ec.gql_mutate_add_tags(per_api_key, tgt_guid, tgt_app_labels)
        update_label_status(all_apps_status, result, tgt_app_labels, tgt_app_name)


def update_label_status(all_apps_status, result, tgt_app_labels, tgt_app_name):
    all_apps_status[tgt_app_name] = {appkeys.STATUS: result['status']}
    if 'error' in result:
        all_apps_status[tgt_app_name][appkeys.ERROR] = result['error']
    else:
        all_apps_status[tgt_app_name][appkeys.LABELS] = tgt_app_labels


def migrate_apps(from_file, src_acct, src_api_key, per_api_key,
                 tgt_acct, tgt_api_key, migrate_list=DEFAULT_MIGRATE_LIST):
    all_apps_status = {}
    if MIGRATE_LABELS in migrate_list:
        migrate_labels(from_file, src_acct, src_api_key, per_api_key, tgt_acct, all_apps_status)
    if MIGRATE_SETTINGS in migrate_list:
        migrate_settings(from_file, src_api_key, tgt_api_key, all_apps_status)
    file_name = utils.file_name_from(from_file)
    status_csv = src_acct + "_" + file_name + "_migrate_apm_" + tgt_acct + ".csv"
    store.save_status_csv(status_csv, all_apps_status, appkeys)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate Labels for list of apps from one account to another')
    setup_params(parser)
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('sourceApiKey', 'ENV_SOURCE_API_KEY')
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('targetApiKey', 'ENV_TARGET_API_KEY')
    personal_api_key = utils.ensure_personal_api_key(args)
    if not personal_api_key:
        utils.error_and_exit('personalApiKey', 'ENV_PERSONAL_API_KEY')
    if not args.settings and not args.labels:
        logger.error("One or both of --labels or --settings must be passed")
    print_args(source_api_key, target_api_key, personal_api_key)
    mig_list = []
    if args.labels:
        mig_list.append(MIGRATE_LABELS)
    if args.settings:
        mig_list.append(MIGRATE_SETTINGS)
    migrate_apps(args.fromFile[0], args.sourceAccount[0], source_api_key, personal_api_key,
                 args.targetAccount[0], target_api_key, mig_list)
