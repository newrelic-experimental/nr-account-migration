import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac
import library.clients.monitorsclient as mc
import library.clients.entityclient as ec

logger = logger.get_logger(os.path.basename(__file__))


def migrate(all_alert_status, policy_name, src_api_key, src_region, src_policy,
            tgt_acct_id, tgt_api_key, tgt_region, tgt_policy, match_source_status):
    logger.info('Loading source synthetic conditions ')
    synth_conditions = ac.get_synthetic_conditions(src_api_key, src_policy['id'], src_region)[ac.SYNTH_CONDITIONS]
    logger.info('Found synthetic conditions ' + str(len(synth_conditions)))
    logger.info('Loading target synthetic conditions ' + policy_name)
    tgt_synth_conds = ac.synth_conditions_by_name_monitor(tgt_api_key, tgt_policy['id'], tgt_region)
    condition_num = 0
    for synth_condition in synth_conditions:
        condition_num = condition_num + 1
        condition_row = policy_name + '-scon' + str(condition_num)
        src_monitor_id = synth_condition[ac.MONITOR_ID]
        src_monitor_name = mc.MonitorsClient.get_monitor(src_api_key, src_monitor_id, src_region)['monitor']['name']
        all_alert_status[condition_row] = {cs.COND_NAME: synth_condition['name']}
        all_alert_status[condition_row][cs.SRC_MONITOR] = src_monitor_name
        result = ec.gql_get_matching_entity_by_name(tgt_api_key, ec.SYNTH_MONITOR, src_monitor_name,
                                                    tgt_acct_id, tgt_region)
        if result['entityFound']:
            tgt_monitor = result['entity']
            all_alert_status[condition_row][cs.TGT_ACCOUNT] = tgt_monitor['accountId']
            all_alert_status[condition_row][cs.TGT_MONITOR] = tgt_monitor['name']
            logger.info('Found matching target monitor ' + tgt_monitor['name'])
            tgt_key = synth_condition['name'] + tgt_monitor['monitorId']
            if tgt_key not in tgt_synth_conds:
                logger.info('Creating target synthetic condition ' + synth_condition['name'])
                tgt_condition = create_tgt_synth_condition(synth_condition, tgt_monitor['monitorId'],
                                                           match_source_status)
                result = ac.create_synthetic_condition(tgt_api_key, tgt_policy, tgt_condition,
                                                       tgt_monitor['name'], tgt_region)
                all_alert_status[condition_row][cs.STATUS] = result['status']
                if 'error' in result.keys():
                    all_alert_status[condition_row][cs.ERROR] = result['error']
            else:
                logger.info('Target has matching condition name-monitor. Skipping condition ' +
                            str(tgt_synth_conds[tgt_key]))
                all_alert_status[condition_row][cs.COND_EXISTED_TARGET] = str(tgt_synth_conds[tgt_key][ac.MONITOR_ID])
        else:
            all_alert_status[condition_row][cs.TGT_MONITOR] = 'NOT_FOUND'
            logger.warn('No matching entity found in target account ' + src_monitor_name)
            logger.warn('Condition skipped ' + str(synth_condition))


def create_tgt_synth_condition(synth_condition, tgt_monitor_id, match_source_status):
    tgt_condition = synth_condition.copy()
    tgt_condition.pop('id')
    if match_source_status == False:
        tgt_condition['enabled'] = False
    tgt_condition[ac.MONITOR_ID] = tgt_monitor_id
    return tgt_condition