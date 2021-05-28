import requests
import os
import json
import library.migrationlogger as migrationlogger
import library.utils as utils
import library.localstore as store
import re
import library.clients.entityclient as ec
from library.clients.endpoints import Endpoints

logger = migrationlogger.get_logger(os.path.basename(__file__))

POLICIES = "policies"
CONDITIONS = 'conditions'
ENTITIES = 'entities'
CONDITION = 'condition'
SYNTH_CONDITIONS = 'synthetics_conditions'
SYNTH_CONDITION = 'synthetics_condition'
LOCATION_FAILURE_CONDITIONS = 'location_failure_conditions'
LOCATION_FAILURE_CONDITION = 'location_failure_condition'
NRQL_CONDITIONS = 'nrql_conditions'
NRQL_CONDITION = 'nrql_condition'
EXTSVC_CONDITIONS = 'external_service_conditions'
EXTSVC_CONDITION = 'external_service_condition'
INFRA_CONDITIONS = 'data'
INFRA_CONDITION = 'data'
INFRA_PAGINATION = 'infra'
CHANNELS = "channels"
ENTITY_CONDITIONS = 'entity_conditions'
MONITOR_ID = 'monitor_id'
SOURCE_POLICY_ID = 'source_policy_id'
POLICY_NAME = 'policy_name'


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'application/json'}


def get_all_alert_policies(api_key, region=Endpoints.REGION_US):
    return utils.get_paginated_entities(api_key, Endpoints.of(region).ALERT_POLICIES_URL, POLICIES)


def get_policy(api_key, name, region=Endpoints.REGION_US):
    filter_params = {'filter[name]': name, 'filter[exact_match]': True}
    result = {'policyFound': False}
    response = requests.get(Endpoints.of(region).ALERT_POLICIES_URL, headers=setup_headers(api_key), params=filter_params)
    result['status'] = response.status_code
    if response.status_code in [200, 304]:
        policies = response.json()['policies']
        if len(policies) > 0:
            result['policyFound'] = True
            result['policy'] = policies[0]
    else:
        if response.text:
            logger.error('Error fetching policy ' + name + ' : ' + response.text)
            result['error'] = response.text
    return result


def get_channels(api_key, region=Endpoints.REGION_US):
    return utils.get_paginated_entities(api_key, Endpoints.of(region).ALERTS_CHANNEL_URL, CHANNELS)


def get_synthetic_conditions(api_key, alert_id, region=Endpoints.REGION_US):
    params = {'policy_id': alert_id}
    return utils.get_paginated_entities(api_key, Endpoints.of(region).GET_SYNTH_CONDITIONS_URL, SYNTH_CONDITIONS, params)


def get_location_failure_conditions(api_key, policy_id, region=Endpoints.REGION_US):
    get_url = Endpoints.of(region).LOC_FAILURE_CONDITIONS_URL + str(policy_id) + '.json'
    return utils.get_paginated_entities(api_key, get_url, LOCATION_FAILURE_CONDITIONS)


def get_nrql_conditions(api_key, account_id, policy_id, region):
    return ec.get_nrql_conditions(api_key, account_id, policy_id, region)


def nrql_conditions_by_name(api_key, account_id, policy_id, region):
    conditions_by_name = {}
    result = get_nrql_conditions(api_key, account_id, policy_id, region)
    if result['error']:
        return {
            'error': result['error'],
            'conditions_by_name': None
        }

    for nrql_condition in result['conditions']:
        conditions_by_name[nrql_condition['name']] = nrql_condition

    return {
        'error': result['error'],
        'conditions_by_name': conditions_by_name
    }


def create_nrql_condition(
    api_key,
    region,
    account_id,
    policy_id,
    nrql_condition,
    nrql_condition_type
):
    return ec.create_nrql_condition(
        api_key,
        region,
        account_id,
        policy_id,
        nrql_condition,
        nrql_condition_type
)


def get_app_conditions(api_key, alert_id, region=Endpoints.REGION_US):
    params = {'policy_id': alert_id}
    return utils.get_paginated_entities(api_key, Endpoints.of(region).GET_APP_CONDITIONS_URL, CONDITIONS, params)


def get_extsvc_conditions(api_key, policy_id, region=Endpoints.REGION_US):
    params = {'policy_id': policy_id}
    return utils.get_paginated_entities(api_key, Endpoints.of(region).EXTSVC_CONDITIONS_URL, EXTSVC_CONDITIONS, params)


def get_infra_conditions(api_key, policy_id, region=Endpoints.REGION_US):
    params = {'policy_id': policy_id, 'limit': 50, 'offset': 0}
    return utils.get_paginated_entities(api_key, Endpoints.of(region).INFRA_CONDITIONS_URL, INFRA_CONDITIONS, params, INFRA_PAGINATION)


def get_entity_conditions(api_key, entity_id, entity_type, region=Endpoints.REGION_US):
    url = '%s/%s.json' % (Endpoints.of(region).ENTITY_CONDITIONS_URL, str(entity_id))
    params = {'entity_type': entity_type}
    return utils.get_paginated_entities(api_key, url, ENTITY_CONDITIONS, params)


def create_channel(api_key, channel, region=Endpoints.REGION_US):
    target_channel = {'channel': {'name': channel['name'], 'type': channel['type']}}
    if 'configuration' in channel:
        target_channel['channel']['configuration'] = channel['configuration']
    prepare_channel(target_channel['channel'])
    result = {}
    response = requests.post(Endpoints.of(region).ALERTS_CHANNEL_URL, headers=setup_headers(api_key),
                             data=json.dumps(target_channel, indent=2))
    result['status'] = response.status_code
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
    else:
        logger.info("Created channel " + channel['name'])
        result['channel'] = response.json()['channels'][0]
    return result


def prepare_channel(channel):
    if channel['type'] == 'webhook':
        if 'headers' in channel['configuration'] and not channel['configuration']['headers']:
            channel['configuration'].pop('headers')  # remove empty headers
        if 'auth_username' in channel['configuration']:
            if 'auth_password' not in channel['configuration']:
                channel['configuration']['auth_password'] = 'dummy'
    if channel['type'] == 'opsgenie':
        if 'api-key' not in channel['configuration']:
            channel['configuration']['api_key'] = 'dummy-dummy-dummy'
    if channel['type'] == 'pagerduty':
        if 'configuration' not in channel:
            channel['configuration'] = {}
        if 'service_key' not in channel['configuration']:
            channel['configuration']['service_key'] = 'dummy-dummy-dummy'
    if channel['type'] == 'slack':
        if 'url' not in channel['configuration']:
            channel['configuration']['url'] = 'dummy-dummy-dummy'


def put_channel_ids(api_key, policy_id, channel_ids, region=Endpoints.REGION_US):
    param_channels = ','.join(str(e) for e in channel_ids)
    params = {'policy_id': policy_id, 'channel_ids': param_channels}
    result = {}
    response = requests.put(Endpoints.of(region).ALERT_POLICY_CHANNELS_URL, headers=setup_headers(api_key),
                            params=params)
    result['status'] = response.status_code
    if response.status_code == 200:
        result['channel_ids'] = response.json()['policy']['channel_ids']
        logger.info('Updated policy with notification channels ' + str(result['channel_ids']))
    else:
        if response.text:
            result['error'] = response.text
            logger.error("Error updating channels in alert policy " + response.text)
    return result


def create_alert_policy(api_key, source_policy, region=Endpoints.REGION_US):
    policy_name = source_policy['name']
    alert_policy = {'policy': {'incident_preference': source_policy['incident_preference'], 'name': policy_name}}
    result = {'entityCreated': False}
    logger.info('Using endpoint ' + Endpoints.of(region).ALERT_POLICIES_URL)
    response = requests.post(Endpoints.of(region).ALERT_POLICIES_URL, headers=setup_headers(api_key),
                             data=json.dumps(alert_policy))
    result['status'] = response.status_code
    if response.status_code != 201:
        logger.error("Error creating : " + policy_name)
        if response.text:
            result['error'] = response.text
            logger.error("Error Message " + response.text)
    else:
        result['entityCreated'] = True
        logger.info("Created : " + policy_name)
        result['policy'] = response.json()['policy']
    return result


def delete_policy(api_key, policy_id, region=Endpoints.REGION_US):
    delete_url = Endpoints.of(region).DEL_ALERTS_URL + str(policy_id) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info(result.url)
    return result


def delete_channel(api_key, channel_id, region=Endpoints.REGION_US):
    delete_url = Endpoints.of(region).DEL_CHANNELS_URL + str(channel_id) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info(result.url)
    return result


def delete_all_policies(api_key, account_id, region=Endpoints.REGION_US):
    logger.warn('Deleting all alert policies for account ' + str(account_id))
    result = get_all_alert_policies(api_key, region)
    if result['response_count'] > 0:
        for policy in result[POLICIES]:
            logger.info('Deleting ' + policy['name'])
            result = delete_policy(api_key, policy['id'], region)
            logger.info('Delete status ' + str(result.status_code))


def delete_all_channels(api_key, account_id, region=Endpoints.REGION_US):
    logger.warn('Deleting all notification channels for account ' + str(account_id))
    result = get_channels(api_key)
    if result['response_count'] > 0:
        for channel in result[CHANNELS]:
            logger.info('Deleting ' + channel['name'])
            result = delete_channel(api_key, channel['id'], region)
            logger.info('Delete status ' + str(result.status_code))


def create_synthetic_condition(api_key, alert_policy, synth_condition, monitor_name, region=Endpoints.REGION_US):
    create_condition_url = Endpoints.of(region).CREATE_SYNTHETICS_CONDITION_URL + str(alert_policy['id']) + '.json'
    payload = {SYNTH_CONDITION: synth_condition}
    response = requests.post(create_condition_url, headers=setup_headers(api_key),
                             data=json.dumps(payload))
    result = {'status': response.status_code}
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating synthetics alert condition for " + monitor_name + " : " +
                         str(response.status_code) + " : " + response.text)
    return result


def create_loc_failure_condition(api_key, alert_policy, loc_failure_condition, region=Endpoints.REGION_US):
    create_condition_url = Endpoints.of(region).LOC_FAILURE_CONDITIONS_URL + str(alert_policy['id']) + '.json'
    payload = {LOCATION_FAILURE_CONDITION: loc_failure_condition}
    response = requests.post(create_condition_url, headers=setup_headers(api_key),
                             data=json.dumps(payload))
    result = {'status': response.status_code}
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating location failure condition " + loc_failure_condition['name'] + " for policy "
                         + alert_policy['name'] + " : " + str(response.status_code) + " : " + response.text)
    return result


def create_app_condition(api_key, alert_policy, app_condition, region=Endpoints.REGION_US):
    return create_alert_condition(api_key, Endpoints.of(region).CREATE_APP_CONDITION_URL, CONDITION, alert_policy, app_condition)


def create_alert_condition(api_key, create_url, cond_key, alert_policy, condition):
    create_condition_url = create_url + str(alert_policy['id']) + '.json'
    payload = {cond_key: condition}
    result = {}
    response = requests.post(create_condition_url, headers=setup_headers(api_key),
                             data=json.dumps(payload))
    result['status'] = response.status_code
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating app condition for " + alert_policy['name'] +
                         " : " + condition['name'] + ":" + str(response.status_code) + " : " + response.text)
    return result


def create_extsvc_condition(api_key, alert_policy, condition, region=Endpoints.REGION_US):
    return create_alert_condition(api_key, Endpoints.of(region).CREATE_EXTSVC_CONDITION_URL, EXTSVC_CONDITION, alert_policy, condition)


def create_infra_condition(api_key, alert_policy, condition, region=Endpoints.REGION_US):
    payload = {INFRA_CONDITION: condition}
    result = {}
    response = requests.post(Endpoints.of(region).CREATE_INFRA_CONDITION_URL, headers=setup_headers(api_key),
                             data=json.dumps(payload))
    result['status'] = response.status_code
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating app condition for " + alert_policy['name'] +
                         " : " + condition['name'] + ":" + str(response.status_code) + " : " + response.text)
    return result


def delete_condition(api_key, alert_policy, app_condition, region=Endpoints.REGION_US):
    delete_url = Endpoints.of(region).APP_CONDITIONS_URL + str(app_condition['id']) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info('Delete status for ' + alert_policy['name'] + ':' + app_condition['name'] + str(result.status_code))


def synth_conditions_by_name_monitor(api_key, policy_id, region=Endpoints.REGION_US):
    conditions_by_name_monitor = {}
    synth_conditions = get_synthetic_conditions(api_key, policy_id, region)[SYNTH_CONDITIONS]
    for synth_condition in synth_conditions:
        if synth_condition[MONITOR_ID]:
            conditions_by_name_monitor[synth_condition['name'] + synth_condition[MONITOR_ID]] = synth_condition
    return conditions_by_name_monitor


def loc_conditions_by_name_monitor(api_key, policy_id, region=Endpoints.REGION_US):
    conditions_by_name_monitor = {}
    loc_conditions = get_location_failure_conditions(api_key, policy_id, region)[LOCATION_FAILURE_CONDITIONS]
    for loc_condition in loc_conditions:
        for entity_id in loc_condition['entities']:
            conditions_by_name_monitor[loc_condition['name'] + entity_id] = loc_condition
    return conditions_by_name_monitor


def app_conditions_by_name_entity(api_key, policy_id):
    conditions_by_name_entity = {}
    app_conditions = get_app_conditions(api_key, policy_id)[CONDITIONS]
    for app_condition in app_conditions:
        for entity_id in app_condition['entities']:
            conditions_by_name_entity[app_condition['name'] + str(entity_id)] = app_condition
    return conditions_by_name_entity


def infra_conditions_by_name(api_key, policy_id, region):
    conditions_by_name = {}
    infra_conditions = get_infra_conditions(api_key, policy_id, region)[INFRA_CONDITIONS]
    for infra_condition in infra_conditions:
        conditions_by_name[infra_condition['name']] = infra_condition
    return conditions_by_name


def get_alert_status_file_name(fromFile, fromFileEntities, src_account_id, tgt_account_id):
    status_file_name = str(src_account_id) + '_'
    if fromFile:
        status_file_name += utils.file_name_from(fromFile) + '_'
    if fromFileEntities:
        status_file_name += utils.file_name_from(fromFileEntities) + '_'
    return status_file_name + str(tgt_account_id) + '_conditions.csv'


def get_policy_entity_map(api_key, alert_policies, region=Endpoints.REGION_US):
    entities_by_policy = {}
    policies_by_entity = {}
    for policy in alert_policies:
        policy_id = policy['id']
        policy_name = policy['name']
        apps = []
        logger.info('Loading app entity conditions for policy ID %d...' % policy_id)
        conditions = get_app_conditions(api_key, policy_id, region)
        if not 'response_count' in conditions or conditions['response_count'] == 0:
            logger.info('No app entity conditions found for policy ID %d' % policy_id)
            entities_by_policy[policy_name] = []
            continue
        
        logger.info('%d app entity conditions found for policy ID %d. Mapping to app entities.' % (conditions['response_count'], policy_id))

        for condition in conditions['conditions']:
            entities = condition['entities']
            for entity_id in entities:
                if not entity_id in apps:
                    apps.append(entity_id)

                if not entity_id in policies_by_entity:
                    policies_by_entity[entity_id] = []

                if not policy_name in policies_by_entity[entity_id]:
                    policies_by_entity[entity_id].append(policy_name)

        entities_by_policy[policy_name] = apps 

    return {
        'entities_by_policy': entities_by_policy,
        'policies_by_entity': policies_by_entity
    }


def get_policy_names_by_entities(entity_names, account_id, api_key, use_local, region=Endpoints.REGION_US):
    names = []
    if use_local:
        alert_policy_entity_map = store.load_alert_policy_entity_map(account_id)
    else:
        alert_policies = get_all_alert_policies(api_key, region)
        alert_policy_entity_map = get_policy_entity_map(api_key, alert_policies['policies'])
    
    policies_by_entity = alert_policy_entity_map['policies_by_entity']

    for entity_name in entity_names:
        entity_id = None
        if entity_name.isnumeric():
            entity_id = entity_name
        else:
            entity_type = ec.APM_APP
            match = re.match(r'(%s|%s|%s|%s)\.(.+)' % (ec.APM_APP, ec.BROWSER_APP, ec.MOBILE_APP, ec.APM_KT), entity_name)
            if match:
                entity_type = match.group(1)
                entity_name = match.group(2)
            result = ec.get_entity_by_name(api_key, account_id, entity_type, entity_name, region)
            if not result['entityFound']:
                continue
            entity = result['entity']
            logger.info('Found entity for entity named %s' % entity_name)
            if entity_type == ec.APM_KT:
                entity_id = str(entity['id'])
            else:
                entity_id = str(entity['applicationId'])
        
        if entity_id in policies_by_entity and len(policies_by_entity[entity_id]) > 0:
            names.extend(policies_by_entity[entity_id])

    return names
