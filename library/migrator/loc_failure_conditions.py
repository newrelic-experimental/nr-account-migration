import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac
import library.clients.monitorsclient as mc
import library.clients.entityclient as ec

logger = logger.get_logger(os.path.basename(__file__))


def migrate(all_alert_status, per_api_key, policy_name, src_api_key, src_policy, tgt_acct_id, tgt_api_key, tgt_policy, match_source_status):
    logger.info('Loading source location failure conditions ')
    result = ac.get_location_failure_conditions(src_api_key, src_policy['id'])
    loc_conds = []
    if result['response_count'] > 0:
        logger.info('location failure response count ' + str(result['response_count']))
        loc_conds = result[ac.LOCATION_FAILURE_CONDITIONS]
    logger.info('Fetched conditions ' + str(len(loc_conds)))
    logger.info('Loading target loc failure conditions')
    tgt_loc_conds = ac.loc_conditions_by_name_monitor(tgt_api_key, tgt_policy['id'])
    condition_num = 0
    for loc_condition in loc_conds:
        condition_num = condition_num + 1
        condition_row = policy_name + '-sloccon' + str(condition_num)
        tgt_entities = []
        for entity_id in loc_condition['entities']:
            src_monitor_name = mc.get_monitor(src_api_key, entity_id)['monitor']['name']
            all_alert_status[condition_row] = {cs.COND_NAME: loc_condition['name']}
            all_alert_status[condition_row][cs.SRC_MONITOR] = src_monitor_name
            result = ec.gql_get_matching_entity_by_name(per_api_key, ec.SYNTH_MONITOR, src_monitor_name, tgt_acct_id)
            if not result['entityFound']:
                all_alert_status[condition_row][cs.TGT_MONITOR] = 'NOT_FOUND'
                logger.warn('No matching entity found in target account ' + src_monitor_name)
            else:
                tgt_monitor = result['entity']
                all_alert_status[condition_row][cs.TGT_ACCOUNT] = tgt_monitor['accountId']
                all_alert_status[condition_row][cs.TGT_MONITOR] = tgt_monitor['name']
                logger.info('Found matching target monitor ' + tgt_monitor['name'])
                tgt_key = loc_condition['name'] + tgt_monitor['monitorId']
                if tgt_key not in tgt_loc_conds:
                    tgt_entities.append(tgt_monitor['monitorId'])
                else:
                    logger.info('Found matching condition name-monitor.Skipping monitor ' + str(tgt_loc_conds[tgt_key]))
                    all_alert_status[condition_row][cs.COND_EXISTED_TARGET] = tgt_key
        if len(tgt_entities) > 0:
            logger.info('Creating target synthetic condition ' + loc_condition['name'])
            tgt_condition = create_tgt_loc_condition(loc_condition, tgt_entities, match_source_status)
            result = ac.create_loc_failure_condition(tgt_api_key, tgt_policy, tgt_condition)
            all_alert_status[condition_row][cs.STATUS] = result['status']
            if 'error' in result.keys():
                all_alert_status[condition_row][cs.ERROR] = result['error']


def create_tgt_loc_condition(loc_condition, tgt_entities, match_source_status):
    tgt_condition = loc_condition.copy()
    tgt_condition.pop('id')
    if match_source_status == False:
        tgt_condition['enabled'] = False
    tgt_condition[ac.ENTITIES] = tgt_entities
    return tgt_condition