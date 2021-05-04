import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac

logger = logger.get_logger(os.path.basename(__file__))

def migrate(all_alert_status, policy_name, src_api_key, src_policy, tgt_acct_id, tgt_api_key, tgt_policy, match_source_status):
    logger.info('Loading source infrastructure conditions ')
    infra_conditions = ac.get_infra_conditions(src_api_key, src_policy['id'])[ac.INFRA_CONDITIONS]
    logger.info('Found infrastructure conditions ' + str(len(infra_conditions)))
    logger.info('Loading target infrastructure conditions ' + policy_name)
    tgt_infra_conds = ac.infra_conditions_by_name(tgt_api_key, tgt_policy['id'])
    condition_num = 0
    for infra_condition in infra_conditions:
        condition_num = condition_num + 1
        condition_row = policy_name + '-infracon' + str(condition_num)
        all_alert_status[condition_row] = {cs.COND_NAME: infra_condition['name']}
        if infra_condition['name'] not in tgt_infra_conds:
            logger.info('Creating target infrastructure condition ' + infra_condition['name'])
            tgt_condition = create_tgt_infra_condition(infra_condition, tgt_policy['id'], match_source_status)
            result = ac.create_infra_condition(tgt_api_key, tgt_policy, tgt_condition)
            all_alert_status[condition_row][cs.STATUS] = result['status']
            if 'error' in result.keys():
                all_alert_status[condition_row][cs.ERROR] = result['error']

def create_tgt_infra_condition(infra_condition, tgt_pol_id, match_source_status):
    tgt_condition = infra_condition.copy()
    tgt_condition.pop('id')
    tgt_condition.pop('created_at_epoch_millis')
    tgt_condition.pop('updated_at_epoch_millis')
    tgt_condition['policy_id'] = tgt_pol_id
    if match_source_status == False:
        tgt_condition['enabled'] = False
    return tgt_condition