import os
import library.status.conditionstatus as cs
import library.migrationlogger as logger
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
import library.utils as utils

logger = logger.get_logger(os.path.basename(__file__))


def migrate(all_alert_status, policy_name, src_api_key, src_policy, tgt_acct_id, tgt_api_key, tgt_policy, match_source_status):
    logger.info('loading source app conditions')
    all_app_conditions = ac.get_app_conditions(src_api_key, src_policy['id'])[ac.CONDITIONS]
    logger.info("Found app alert conditions " + str(len(all_app_conditions)))
    tgt_app_conds = ac.app_conditions_by_name_entity(tgt_api_key, tgt_policy['id'])
    condition_num = 0
    for app_condition in all_app_conditions:
        condition_num = condition_num + 1
        entity_type = utils.get_entity_type(app_condition)
        condition_row = create_condition_status_row(all_alert_status, app_condition, condition_num, entity_type, policy_name)
        entity_ids = app_condition[ac.ENTITIES]
        tgt_entities = []
        tgt_existing = []
        for entity_id in entity_ids:
            result = ec.get_entity(src_api_key, entity_type, entity_id)
            if not result['entityFound']:
                status_src_not_found(all_alert_status, condition_row, entity_type, entity_id)
                continue
            src_entity = result['entity']
            logger.info('source entity found ' + str(src_entity['id']))
            if entity_type == ec.APM_KT:
                result = ec.get_matching_kt(tgt_api_key,src_entity['name'])
            else:
                result = ec.gql_get_matching_entity(tgt_api_key, entity_type, src_entity, tgt_acct_id)
            if not result['entityFound']:
                status_tgt_not_found(all_alert_status, condition_row, src_entity, app_condition)
                continue
            tgt_entity = result['entity']
            if entity_type == ec.APM_KT:
                tgt_id = str(tgt_entity['id'])
                tgt_key = app_condition['name'] + tgt_id
            else:
                tgt_id = str(tgt_entity['applicationId'])
                tgt_key = app_condition['name'] + tgt_id
            if tgt_key not in tgt_app_conds.keys():
                logger.info('New Target entity found ' + str(tgt_acct_id) + ":" + tgt_entity['name'])
                tgt_entities.append(tgt_id)
            else:
                tgt_existing.append(tgt_id)
                logger.info('Skipping as policy already contains a condition by this name for this entity ' + tgt_key)
        if len(tgt_entities) > 0:
            update_condition_status(all_alert_status, condition_row, entity_ids, tgt_acct_id,
                                    tgt_entities)
            tgt_condition = create_tgt_app_condition(app_condition, tgt_entities, match_source_status)
            result = ac.create_app_condition(tgt_api_key, tgt_policy, tgt_condition)
            all_alert_status[condition_row][cs.STATUS] = result['status']
            if cs.ERROR in result.keys():
                all_alert_status[condition_row][cs.ERROR] = result['error']
        if len(tgt_existing) > 0:
            all_alert_status[condition_row][cs.COND_EXISTED_TARGET] = tgt_existing


def status_tgt_not_found(all_alert_status, condition_row, src_entity, app_condition):
    logger.warn('Entity skipped matching target not found ' + src_entity['name'] + ':' + str(app_condition))
    all_alert_status[condition_row][cs.SRC_ENTITY] = src_entity['name']
    all_alert_status[condition_row][cs.TGT_ENTITY] = 'NOT_FOUND'
    all_alert_status[condition_row][cs.ERROR] = 'TGT_ENTITY_NOT_FOUND'


def status_src_not_found(all_alert_status, condition_row, entity_type, entity_id):
    logger.error('Skipping entity not found in source account '
                 + entity_type + ':' + entity_id)
    all_alert_status[condition_row][cs.SRC_ENTITY] = 'NOT_FOUND'
    all_alert_status[condition_row][cs.ERROR] = 'SRC_ENTITY_NOT_FOUND'


def create_condition_status_row(all_alert_status, app_condition, condition_num, entity_type, policy_name):
    condition_row = policy_name + utils.get_condition_prefix(entity_type) + str(condition_num)
    all_alert_status[condition_row] = {cs.COND_NAME: app_condition['name']}
    return condition_row


def update_condition_status(all_alert_status, condition_row, entity_ids, tgt_acct_id, tgt_entities):
    all_alert_status[condition_row][cs.SRC_ENTITY] = entity_ids
    all_alert_status[condition_row][cs.TGT_ACCOUNT] = tgt_acct_id
    all_alert_status[condition_row][cs.TGT_ENTITY] = tgt_entities


def create_tgt_app_condition(app_condition, tgt_entities, match_source_status):
    tgt_condition = app_condition.copy()
    tgt_condition.pop('id')
    if match_source_status == False:
        tgt_condition['enabled'] = False
    tgt_condition[ac.ENTITIES] = tgt_entities
    return tgt_condition
