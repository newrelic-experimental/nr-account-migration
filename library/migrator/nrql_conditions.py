import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac

logger = logger.get_logger(os.path.basename(__file__))


def migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_acct_id, tgt_api_key, tgt_policy):
    logger.info('Loading NRQL conditions ')
    result = ac.get_nrql_conditions(src_api_key, src_policy['id'])
    nrql_conds = []
    if result['response_count'] > 0:
        logger.info('NRQL conditions response count ' + str(result['response_count']))
        nrql_conds = result[ac.NRQL_CONDITIONS]
    logger.info('Fetched conditions ' + str(len(nrql_conds)))
    logger.info('Loading target NRQL conditions')
    tgt_nrql_conds = ac.nrql_conditions_by_name(tgt_api_key, tgt_policy['id'])
    condition_num = 0
    for nrql_condition in nrql_conds:
        condition_num = condition_num + 1
        condition_row = policy_name + '-nrqlcon' + str(condition_num)
        all_alert_status[condition_row] = {cs.COND_NAME: nrql_condition['name']}
        if nrql_condition['name'] not in tgt_nrql_conds:
            logger.info('Creating target NRQL condition ' + nrql_condition['name'])
            tgt_condition = create_tgt_nrql_condition(nrql_condition)
            result = ac.create_nrql_condition(tgt_api_key, tgt_policy, tgt_condition)
            all_alert_status[condition_row][cs.STATUS] = result['status']
            if 'error' in result.keys():
                all_alert_status[condition_row][cs.ERROR] = result['error']


def create_tgt_nrql_condition(nrql_condition):
    tgt_condition = nrql_condition.copy()
    tgt_condition.pop('id')
    tgt_condition['enabled'] = False
    return tgt_condition