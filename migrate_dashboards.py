import os
import argparse
import library.utils as utils
import library.migrationlogger as m_logger
import library.localstore as store
import library.clients.entityclient as ec
import library.status.dashboard_status as ds


log = m_logger.get_logger(os.path.basename(__file__))


def print_args(src_api_key, tgt_api_key):
    log.info("Using fromFile : " + args.fromFile[0])
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    log.info("Using targetAccount : " + str(args.targetAccount[0]))
    log.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])


def setup_params():
    parser.add_argument('--fromFile', nargs=1, type=str, required=True,
                        help='Path to file with dashboard names(newline separated)')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')


def get_dashboard(per_api_key, name, all_db_status, acct_id, get_widgets = False):
    result = ec.get_dashboard_definition(per_api_key, name, acct_id)
    if not result:
        all_db_status[name][ds.DASHBOARD_FOUND] = False
        return None

    all_db_status[name][ds.DASHBOARD_FOUND] = True
    if not get_widgets:
        return result

    widgets_result = ec.get_dashboard_widgets(per_api_key, result['guid'])
    if 'error' in widgets_result:
        all_db_status[name][ds.ERROR] = result['error']
        log.error('Error fetching dashboard widgets' + name + '  ' + result['error'])
        return None

    if not widgets_result['entityFound']:
        all_db_status[name][ds.WIDGETS_FOUND] = False
        return None

    all_db_status[name][ds.WIDGETS_FOUND] = True
    return widgets_result['entity']


def update_nrql_account_ids(src_acct_id, tgt_acct_id, entity):
    if not 'pages' in entity:
        return

    for page in entity['pages']:
        if not 'widgets' in page:
            continue

        for widget in page['widgets']:
            if not 'rawConfiguration' in widget:
                continue

            if not 'nrqlQueries' in widget['rawConfiguration']:
                continue

            for query in widget['rawConfiguration']['nrqlQueries']:
                if 'accountId' in query and query['accountId'] == src_acct_id:
                    query['accountId'] = tgt_acct_id

def migrate_dashboards(from_file, src_acct, src_api_key, tgt_acct, tgt_api_key):
    log.info('Dashboard migration started.')
    db_names = store.load_names(from_file)
    all_db_status = {}
    for db_name in db_names:
        all_db_status[db_name] = {}
        tgt_dashboard = get_dashboard(tgt_api_key, db_name, all_db_status, tgt_acct)
        if tgt_dashboard is not None:
            log.warning('Dashboard already exists in target skipping : ' + db_name)
            all_db_status[db_name][ds.TARGET_EXISTED] = True
            continue
        all_db_status[db_name][ds.TARGET_EXISTED] = False
        src_dashboard = get_dashboard(src_api_key, db_name, all_db_status, src_acct, True)
        if src_dashboard is None:
            continue
        log.info('Found source dashboard ' + db_name)
        tgt_dashboard = src_dashboard
        del tgt_dashboard['guid']
        update_nrql_account_ids(src_acct, tgt_acct, tgt_dashboard)
        result = ec.post_dashboard(tgt_api_key, tgt_dashboard, tgt_acct)
        all_db_status[db_name][ds.STATUS] = result['status']
        if result['entityCreated']:
            log.info('Created target dashboard ' + db_name)
            all_db_status[db_name][ds.DASHBOARD_CREATED] = True
            all_db_status[db_name][ds.TARGET_DASHBOARD] = result['entity']['guid']
    db_status_file = str(src_acct) + '_' + utils.file_name_from(from_file) + '_dashboards_' + str(tgt_acct) + '.csv'
    store.save_status_csv(db_status_file, all_db_status, ds)
    log.info('Dashboard migration complete.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate Dashboards')
    setup_params()
    args = parser.parse_args()
    source_api_key = utils.ensure_source_api_key(args)
    if not source_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    target_api_key = utils.ensure_target_api_key(args)
    if not target_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    print_args(source_api_key, target_api_key)
    migrate_dashboards(args.fromFile[0], args.sourceAccount[0], source_api_key, args.targetAccount[0], target_api_key)