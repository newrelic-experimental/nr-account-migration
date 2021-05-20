import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac

logger = logger.get_logger(os.path.basename(__file__))


def migrate(all_alert_status, policy_name, src_acct_id, src_api_key, src_policy, tgt_acct_id, tgt_api_key, tgt_policy, match_source_status):
    logger.info('Loading source NRQL conditions ')
    result = ac.get_nrql_conditions(src_api_key, src_acct_id, src_policy['id'])
    if result['error']:
        all_alert_status[policy_name][cs.ERROR] = result['error']
        return
    
    nrql_conds = result['conditions']
    logger.info('Fetched %d source conditions' % len(nrql_conds))

    logger.info('Loading target NRQL conditions')
    result = ac.nrql_conditions_by_name(tgt_api_key, tgt_acct_id, tgt_policy['id'])
    if result['error']:
        all_alert_status[policy_name][cs.ERROR] = result['error']
        return

    tgt_nrql_conds = result['conditions_by_name']
    condition_num = 0
    for nrql_condition in nrql_conds:
        condition_num += 1
        condition_row = policy_name + '-nrqlcon' + str(condition_num)
        all_alert_status[condition_row] = {
            cs.COND_NAME: nrql_condition['name'],
            cs.TGT_ACCOUNT: tgt_acct_id,
            cs.COND_EXISTED_TARGET: 'Y'
        }
        if nrql_condition['name'] not in tgt_nrql_conds:
            all_alert_status[condition_row][cs.COND_EXISTED_TARGET] = 'N'
            logger.info('Creating target NRQL condition %s' % nrql_condition['name'])
            tgt_condition = create_tgt_nrql_condition(nrql_condition, match_source_status)
            result = ac.create_nrql_condition(tgt_api_key, tgt_acct_id, tgt_policy['id'], tgt_condition, nrql_condition['type'])
            all_alert_status[condition_row][cs.STATUS] = result['status']
            if 'error' in result.keys(): 
                all_alert_status[condition_row][cs.ERROR] = result['error']


def create_tgt_nrql_condition(nrql_condition, match_source_status):
    tgt_condition = nrql_condition.copy()
    tgt_condition.pop('id')
    tgt_condition.pop('policyId')
    tgt_condition.pop('type')
    if match_source_status == False:
        tgt_condition['enabled'] = False
    return tgt_condition