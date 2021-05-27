import os
import library.status.conditionstatus as cs
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
import library.utils as utils

log = m_logger.get_logger(os.path.basename(__file__))


def extsvc_conditions_by_name_entity(api_key, policy_id, region):
    conditions_by_name_entity = {}
    extsvc_conditions = ac.get_extsvc_conditions(api_key, policy_id, region)[ac.EXTSVC_CONDITIONS]
    for extsvc_condition in extsvc_conditions:
        for entity_id in extsvc_condition['entities']:
            conditions_by_name_entity[extsvc_condition['name'] + str(entity_id)] = extsvc_condition
    return conditions_by_name_entity


def get_entity_type(extsvc_condition):
    if extsvc_condition['type'] == 'apm_external_service':
        return ec.APM_APP
    if extsvc_condition['type'] == 'mobile_external_service':
        return ec.MOBILE_APP


def migrate(all_alert_status, policy_name, src_api_key, src_region, src_policy,
            tgt_acct_id, tgt_api_key, tgt_region, tgt_policy, match_source_status):
    log.info('loading source ext svc conditions')
    extsvc_conditions = ac.get_extsvc_conditions(src_api_key, src_policy['id'], src_region)[ac.EXTSVC_CONDITIONS]
    if len(extsvc_conditions) <= 0:
        log.info("No external service conditions found.")
        return
    log.info("Found ext svc conditions " + str(len(extsvc_conditions)))
    tgt_extsvc_conds = extsvc_conditions_by_name_entity(tgt_api_key, tgt_policy['id'], tgt_region)
    cond_num = 0
    for extsvc_condition in extsvc_conditions:
        cond_num = cond_num + 1
        entity_type = get_entity_type(extsvc_condition)
        cond_row = create_condition_status_row(all_alert_status, extsvc_condition, cond_num, policy_name)
        entity_ids = extsvc_condition[ac.ENTITIES]
        tgt_entities = []
        tgt_existing = []
        for entity_id in entity_ids:
            result = ec.get_entity(src_api_key, entity_type, entity_id, src_region)
            if not result['entityFound']:
                status_src_not_found(all_alert_status, cond_row, entity_type, entity_id)
                continue
            src_entity = result['entity']
            log.info('source entity found ' + str(src_entity['id']))
            result = ec.gql_get_matching_entity(tgt_api_key, entity_type, src_entity, tgt_acct_id, tgt_region)
            if not result['entityFound']:
                status_tgt_not_found(all_alert_status, cond_row, src_entity, extsvc_condition)
                continue
            tgt_entity = result['entity']
            tgt_id = str(tgt_entity['applicationId'])
            tgt_key = extsvc_condition['name'] + tgt_id
            if tgt_key not in tgt_extsvc_conds.keys():
                log.info('New Target entity found ' + str(tgt_acct_id) + ":" + tgt_entity['name'])
                tgt_entities.append(tgt_id)
            else:
                tgt_existing.append(tgt_id)
                log.info('Skipping as policy already contains a condition by this name for this entity ' + tgt_key)
        if len(tgt_entities) > 0:
            update_condition_status(all_alert_status, cond_row, entity_ids, tgt_acct_id,
                                    tgt_entities)
            tgt_condition = create_tgt_extsvc_condition(extsvc_condition, tgt_entities, match_source_status)
            result = ac.create_extsvc_condition(tgt_api_key, tgt_policy, tgt_condition, tgt_region)
            all_alert_status[cond_row][cs.STATUS] = result['status']
            if cs.ERROR in result.keys():
                all_alert_status[cond_row][cs.ERROR] = result['error']
        if len(tgt_existing) > 0:
            all_alert_status[cond_row][cs.COND_EXISTED_TARGET] = tgt_existing


def status_tgt_not_found(all_alert_status, cond_row, src_entity, app_condition):
    log.warn('Entity skipped matching target not found ' + src_entity['name'] + ':' + str(app_condition))
    all_alert_status[cond_row][cs.SRC_ENTITY] = src_entity['name']
    all_alert_status[cond_row][cs.TGT_ENTITY] = 'NOT_FOUND'
    all_alert_status[cond_row][cs.ERROR] = 'TGT_ENTITY_NOT_FOUND'


def status_src_not_found(all_alert_status, cond_row, entity_type, entity_id):
    log.error('Skipping entity not found in source account '
                 + entity_type + ':' + entity_id)
    all_alert_status[cond_row][cs.SRC_ENTITY] = 'NOT_FOUND'
    all_alert_status[cond_row][cs.ERROR] = 'SRC_ENTITY_NOT_FOUND'


def create_condition_status_row(all_alert_status, extsvc_condition, cond_num, policy_name):
    cond_row = policy_name + '-extsvc-' + str(cond_num)
    all_alert_status[cond_row] = {cs.COND_NAME: extsvc_condition['name']}
    return cond_row


def update_condition_status(all_alert_status, condition_row, entity_ids, tgt_acct_id, tgt_entities):
    all_alert_status[condition_row][cs.SRC_ENTITY] = entity_ids
    all_alert_status[condition_row][cs.TGT_ACCOUNT] = tgt_acct_id
    all_alert_status[condition_row][cs.TGT_ENTITY] = tgt_entities


def create_tgt_extsvc_condition(extsvc_condition, tgt_entities, match_source_status):
    tgt_condition = extsvc_condition.copy()
    tgt_condition.pop('id')
    if match_source_status == False:
        tgt_condition['enabled'] = False
    tgt_condition[ac.ENTITIES] = tgt_entities
    return tgt_condition
