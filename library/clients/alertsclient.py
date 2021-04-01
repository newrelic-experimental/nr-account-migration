import requests
import os
import json
import library.migrationlogger as migrationlogger
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))

ALERT_POLICIES_URL = 'https://api.newrelic.com/v2/alerts_policies.json'
DEL_ALERTS_URL = 'https://api.newrelic.com/v2/alerts_policies/'

POLICIES = "policies"

GET_APP_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_conditions.json'
APP_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_conditions/'
CREATE_APP_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_conditions/policies/'
CONDITIONS = 'conditions'
ENTITIES = 'entities'
CONDITION = 'condition'

GET_SYNTH_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_synthetics_conditions.json'
CREATE_SYNTHETICS_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_synthetics_conditions/policies/'
SYNTH_CONDITIONS = 'synthetics_conditions'
SYNTH_CONDITION = 'synthetics_condition'

LOC_FAILURE_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_location_failure_conditions/policies/'
LOCATION_FAILURE_CONDITIONS = 'location_failure_conditions'
LOCATION_FAILURE_CONDITION = 'location_failure_condition'

NRQL_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_nrql_conditions.json'
NRQL_CONDITIONS = 'nrql_conditions'
CREATE_NRQL_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_nrql_conditions/policies/'
NRQL_CONDITION = 'nrql_condition'

EXTSVC_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_external_service_conditions.json'
CREATE_EXTSVC_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_external_service_conditions/policies/'
EXTSVC_CONDITIONS = 'external_service_conditions'
EXTSVC_CONDITION = 'external_service_condition'

ALERTS_CHANNEL_URL = 'https://api.newrelic.com/v2/alerts_channels.json'
DEL_CHANNELS_URL = 'https://api.newrelic.com/v2/alerts_channels/'
CHANNELS = "channels"
ALERT_POLICY_CHANNELS_URL = 'https://api.newrelic.com/v2/alerts_policy_channels.json'

MONITOR_ID = 'monitor_id'
SOURCE_POLICY_ID = 'source_policy_id'
POLICY_NAME = 'policy_name'


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def get_all_alert_policies(api_key):
    return utils.get_paginated_entities(api_key, ALERT_POLICIES_URL, POLICIES)


def get_policy(api_key, name):
    filter_params = {'filter[name]': name, 'filter[exact_match]': True}
    result = {'policyFound': False}
    response = requests.get(ALERT_POLICIES_URL, headers=setup_headers(api_key), params=filter_params)
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


def get_channels(api_key):
    return utils.get_paginated_entities(api_key, ALERTS_CHANNEL_URL, CHANNELS)


def get_synthetic_conditions(api_key, alert_id):
    params = {'policy_id': alert_id}
    return utils.get_paginated_entities(api_key, GET_SYNTH_CONDITIONS_URL, SYNTH_CONDITIONS, params)


def get_location_failure_conditions(api_key, policy_id):
    get_url = LOC_FAILURE_CONDITIONS_URL + str(policy_id) + '.json'
    return utils.get_paginated_entities(api_key, get_url, LOCATION_FAILURE_CONDITIONS)


def get_nrql_conditions(api_key, policy_id):
    params = {'policy_id': policy_id}
    return utils.get_paginated_entities(api_key, NRQL_CONDITIONS_URL, NRQL_CONDITIONS, params)


def nrql_conditions_by_name(api_key, policy_id):
    conditions_by_name = {}
    nrql_conditions = get_nrql_conditions(api_key, policy_id)[NRQL_CONDITIONS]
    for nrql_condition in nrql_conditions:
        conditions_by_name[nrql_condition['name']] = nrql_condition
    return conditions_by_name


def create_nrql_condition(api_key, alert_policy, nrql_condition):
    create_condition_url = CREATE_NRQL_CONDITIONS_URL + str(alert_policy['id']) + '.json'
    payload = {NRQL_CONDITION: nrql_condition}
    response = requests.post(create_condition_url, headers=setup_headers(api_key),
                             data=json.dumps(payload))
    result = {'status': response.status_code}
    if response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating NRQL condition" + nrql_condition['name'] + " for policy " +
                         alert_policy['name'] + " : " + str(response.status_code) + " : " + response.text)
    return result


def get_app_conditions(api_key, alert_id):
    params = {'policy_id': alert_id}
    return utils.get_paginated_entities(api_key, GET_APP_CONDITIONS_URL, CONDITIONS, params)


def get_extsvc_conditions(api_key, policy_id):
    params = {'policy_id': policy_id}
    return utils.get_paginated_entities(api_key, EXTSVC_CONDITIONS_URL, EXTSVC_CONDITIONS, params)


def create_channel(api_key, channel):
    target_channel = {'channel': {'name': channel['name'], 'type': channel['type']}}
    if 'configuration' in channel:
        target_channel['channel']['configuration'] = channel['configuration']
    prepare_channel(target_channel['channel'])
    result = {}
    response = requests.post(ALERTS_CHANNEL_URL, headers=setup_headers(api_key),
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


def put_channel_ids(api_key, policy_id, channel_ids):
    param_channels = ','.join(str(e) for e in channel_ids)
    params = {'policy_id': policy_id, 'channel_ids': param_channels}
    result = {}
    response = requests.put(ALERT_POLICY_CHANNELS_URL, headers=setup_headers(api_key), params=params)
    result['status'] = response.status_code
    if response.status_code == 200:
        result['channel_ids'] = response.json()['policy']['channel_ids']
        logger.info('Updated policy with notification channels ' + str(result['channel_ids']))
    else:
        if response.text:
            result['error'] = response.text
            logger.error("Error updating channels in alert policy " + response.text)
    return result


def create_alert_policy(api_key, source_policy):
    policy_name = source_policy['name']
    alert_policy = {'policy': {'incident_preference': source_policy['incident_preference'], 'name': policy_name}}
    result = {'entityCreated': False}
    response = requests.post(ALERT_POLICIES_URL, headers=setup_headers(api_key), data=json.dumps(alert_policy))
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


def delete_policy(api_key, policy_id):
    delete_url = DEL_ALERTS_URL + str(policy_id) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info(result.url)
    return result


def delete_channel(api_key, channel_id):
    delete_url = DEL_CHANNELS_URL + str(channel_id) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info(result.url)
    return result


def delete_all_policies(api_key, account_id):
    logger.warn('Deleting all alert policies for account ' + str(account_id))
    result = get_all_alert_policies(api_key)
    if result['response_count'] > 0:
        for policy in result[POLICIES]:
            logger.info('Deleting ' + policy['name'])
            result = delete_policy(api_key, policy['id'])
            logger.info('Delete status ' + str(result.status_code))


def delete_all_channels(api_key, account_id):
    logger.warn('Deleting all notification channels for account ' + str(account_id))
    result = get_channels(api_key)
    if result['response_count'] > 0:
        for channel in result[CHANNELS]:
            logger.info('Deleting ' + channel['name'])
            result = delete_channel(api_key, channel['id'])
            logger.info('Delete status ' + str(result.status_code))


def create_synthetic_condition(api_key, alert_policy, synth_condition, monitor_name):
    create_condition_url = CREATE_SYNTHETICS_CONDITION_URL + str(alert_policy['id']) + '.json'
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


def create_loc_failure_condition(api_key, alert_policy, loc_failure_condition):
    create_condition_url = LOC_FAILURE_CONDITIONS_URL + str(alert_policy['id']) + '.json'
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


def create_app_condition(api_key, alert_policy, app_condition):
    return create_alert_condition(api_key, CREATE_APP_CONDITION_URL, CONDITION, alert_policy, app_condition)


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


def create_extsvc_condition(api_key, alert_policy, condition):
    return create_alert_condition(api_key, CREATE_EXTSVC_CONDITION_URL, EXTSVC_CONDITION, alert_policy, condition)


def delete_condition(api_key, alert_policy, app_condition):
    delete_url = APP_CONDITIONS_URL + str(app_condition['id']) + '.json'
    result = requests.delete(delete_url, headers=setup_headers(api_key))
    logger.info('Delete status for ' + alert_policy['name'] + ':' + app_condition['name'] + str(result.status_code))


def synth_conditions_by_name_monitor(api_key, policy_id):
    conditions_by_name_monitor = {}
    synth_conditions = get_synthetic_conditions(api_key, policy_id)[SYNTH_CONDITIONS]
    for synth_condition in synth_conditions:
        if synth_condition[MONITOR_ID]:
            conditions_by_name_monitor[synth_condition['name'] + synth_condition[MONITOR_ID]] = synth_condition
    return conditions_by_name_monitor


def loc_conditions_by_name_monitor(api_key, policy_id):
    conditions_by_name_monitor = {}
    loc_conditions = get_location_failure_conditions(api_key, policy_id)[LOCATION_FAILURE_CONDITIONS]
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
