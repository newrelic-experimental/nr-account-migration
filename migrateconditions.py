import os
import sys
import argparse
import library.localstore as store
import library.clients.alertsclient as ac
import library.migrationlogger as logger
import library.utils as utils
import library.status.conditionstatus as cs
import library.migrator.loc_failure_conditions as lfc_migrator
import library.migrator.synth_conditions as sc_migrator
import library.migrator.app_conditions as ac_migrator
import library.migrator.nrql_conditions as nrql_migrator
import library.migrator.extsvc_conditions as extsvc_migrator
import library.migrator.infra_conditions as infra_migrator

logger = logger.get_logger(os.path.basename(__file__))
SYNTHETICS = 'synthetics'
APP_CONDITIONS = 'app-conditions'
NRQL_CONDITIONS = 'nrql-conditions'
EXT_SVC_CONDITIONS = 'ext-svc-conditions'
INFRA_CONDITIONS = 'infra-conditions'
ALL_CONDITIONS = [SYNTHETICS, APP_CONDITIONS, NRQL_CONDITIONS, EXT_SVC_CONDITIONS, INFRA_CONDITIONS]  # currently used only for testing


def setup_params():
    parser.add_argument('--fromFile', nargs=1, type=str, required=True, help='Path to file with alert policy names')
    parser.add_argument('--personalApiKey', nargs=1, type=str, required=True, help='Personal API Key for GraphQL client \
                                                                    alternately environment variable ENV_PERSONAL_API_KEY')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetAccount', nargs=1, type=str,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=False, help='Target API Key, \
                                                                        or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--synthetics', dest='synthetics', required=False, action='store_true',
                    help='Pass --synthetics to migrate synthetics conditions')
    parser.add_argument('--app_conditions', dest='app_conditions', required=False, action='store_true',
                        help='Pass --app_conditions to migrate app conditions')
    parser.add_argument('--nrql_conditions', dest='nrql_conditions', required=False, action='store_true',
                        help='Pass --nrql_conditions to migrate NRQL conditions')
    parser.add_argument('--ext_svc_conditions', dest='ext_svc_conditions', required=False, action='store_true',
                        help='Pass --ext_svc_conditions to migrate external service conditions')
    parser.add_argument('--infra_conditions', dest='infra_conditions', required=False, action='store_true',
                        help='Pass --infra_conditions to migrate infrastructure conditions')


def print_args(per_api_key, src_api_key, tgt_api_key):
    logger.info("Using fromFile : " + args.fromFile[0])
    logger.info("Using personalApiKey : " + len(per_api_key[:-4])*"*"+per_api_key[-4:])
    logger.info("Using sourceAccount : " + args.sourceAccount[0])
    logger.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    logger.info("Using targetAccount : " + args.targetAccount[0])
    logger.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    if args.synthetics:
        logger.info("Migrating conditions of type " + SYNTHETICS)
    if args.app_conditions:
        logger.info("Migrating conditions of type " + APP_CONDITIONS)
    if args.nrql_conditions:
        logger.info("Migrating conditions of type " + NRQL_CONDITIONS)
    if args.ext_svc_conditions:
        logger.info("Migrating conditions of type " + EXT_SVC_CONDITIONS)
    if args.infra_conditions:
        logger.info("Migrating conditions of type " + INFRA_CONDITIONS)


def migrate_conditions(from_file, per_api_key, src_account_id, src_api_key, tgt_account_id, tgt_api_key, cond_types):
    all_alert_status = {}
    policy_names = store.load_names(from_file)
    for policy_name in policy_names:
        logger.info('Migrating conditions for policy ' + policy_name)
        all_alert_status[policy_name] = {}
        src_result = ac.get_policy(src_api_key, policy_name)
        if not src_result['policyFound']:
            logger.error("Skipping as policy not found in source account " + policy_name)
            all_alert_status[policy_name][cs.ERROR] = 'Policy not found in source account'
            continue
        src_policy = src_result['policy']
        tgt_result = ac.get_policy(tgt_api_key, policy_name)
        if not tgt_result['policyFound']:
            logger.error("Skipping as policy not found in target account " + policy_name)
            all_alert_status[policy_name][cs.ERROR] = 'Policy not found in target account'
            continue
        tgt_policy = tgt_result['policy']
        if SYNTHETICS in cond_types:
            sc_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy,
                                tgt_account_id, tgt_api_key, tgt_policy)
            lfc_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy,
                                 tgt_account_id, tgt_api_key, tgt_policy)
        if APP_CONDITIONS in cond_types:
            ac_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_account_id,
                                tgt_api_key, tgt_policy)
        if NRQL_CONDITIONS in cond_types:
            nrql_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_account_id,
                                tgt_api_key, tgt_policy)
        if EXT_SVC_CONDITIONS in cond_types:
            extsvc_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_account_id,
                                  tgt_api_key, tgt_policy)
        if INFRA_CONDITIONS in cond_types:
            infra_migrator.migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_account_id, 
                                tgt_api_key, tgt_policy)
    status_file = src_account_id + '_' + utils.file_name_from(from_file) + '_' + tgt_account_id + '_conditions.csv'
    store.save_status_csv(status_file, all_alert_status, cs)


def parse_condition_types(args):
    condition_types = []
    if args.synthetics:
        condition_types.append(SYNTHETICS)
    if args.app_conditions:
        condition_types.append(APP_CONDITIONS)
    if args.nrql_conditions:
        condition_types.append(NRQL_CONDITIONS)
    if args.ext_svc_conditions:
        condition_types.append(EXT_SVC_CONDITIONS)
    if args.infra_conditions:
        condition_types.append(INFRA_CONDITIONS)
    return condition_types


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate Alert Conditions from source to target policy')
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
    cond_types = parse_condition_types(args)
    if len(cond_types) == 0:
        logger.error('At least one condition type must be specified currently supported ' +
                     SYNTHETICS + ',' + APP_CONDITIONS + ',' + NRQL_CONDITIONS + ',' + INFRA_CONDITIONS)
        sys.exit()
    print_args(personal_api_key, source_api_key, target_api_key)
    logger.info('Starting Alert Conditions Migration')
    migrate_conditions(args.fromFile[0], personal_api_key, args.sourceAccount[0], source_api_key, args.targetAccount[0],
                       target_api_key, cond_types)
    logger.info('Done Alert Conditions Migration')