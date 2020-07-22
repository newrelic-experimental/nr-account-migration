import requests
import json
import os
import library.migrationlogger as m_logger
import library.utils as utils


APM_APP = 'APM_APP'
APM_KT = 'APM_KT'
BROWSER_APP = 'BROWSER_APP'
APM_EXT_SVC = 'APM_EXT_SVC'
MOBILE_APP = 'MOBILE_APP'
SYNTH_MONITOR = 'SYNTH_MONITOR'

GRAPHQL_URL = 'https://api.newrelic.com/graphql'
SHOW_APM_APP_URL = 'https://api.newrelic.com/v2/applications/'
GET_APM_APP_URL = 'https://api.newrelic.com/v2/applications.json'
GET_BROWSER_APP_URL = 'https://api.newrelic.com/v2/browser_applications.json'
SHOW_MOBILE_APP_URL = 'https://api.newrelic.com/v2/mobile_applications/'
SHOW_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions/'
GET_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions.json'
KEY_TRANSACTIONS = 'key_transactions'
PUT_LABEL_URL = 'https://api.newrelic.com/v2/labels.json'
GET_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards.json'
DASHBOARDS = 'dashboards'
SHOW_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards/'
DEL_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards/'

logger = m_logger.get_logger(os.path.basename(__file__))


def rest_api_headers(api_key):
    return {'X-Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def gql_headers(api_key):
    return {'api-key': api_key, 'Content-Type': 'application/json'}


def entity_outline(entity_type):
    if entity_type == APM_APP:
        return ''' ... on ApmApplicationEntityOutline {
                        guid
                        applicationId
                        name
                        accountId
                        type
                        language
                        entityType
                    } '''
    if entity_type == BROWSER_APP:
        return ''' ... on BrowserApplicationEntityOutline {
                                guid
                                applicationId
                                name
                                accountId
                                type
                                entityType
                            } '''
    if entity_type == MOBILE_APP:
        return ''' ... on MobileApplicationEntityOutline {
                        guid
                        applicationId
                        name
                        accountId
                        type                        
                        entityType
                    } '''
    if entity_type == SYNTH_MONITOR:
        return ''' ... on SyntheticMonitorEntityOutline {
                            guid
                            entityType
                            accountId
                            monitorId
                            name                            
                            monitorType 
                        }  '''


def search_query_payload(entity_type, entity_name):
    gql_search_type = 'APPLICATION'
    if entity_type == SYNTH_MONITOR:
        gql_search_type = 'MONITOR'
    entity_search_query = '''query($matchingCondition: String!) { 
                                    actor { 
                                        entitySearch(query: $matchingCondition)  { 
                                            count 
                                            results { 
                                                entities { ''' + entity_outline(entity_type) + '''
                                                } 
                                            } 
                                        } 
                                    } 
                                }
                                '''
    variables = {'matchingCondition': "name = '" + entity_name + "' AND type = '"+gql_search_type+"'"}
    payload = {'query': entity_search_query, 'variables': variables}
    return payload


def matched_apm_app(entity, tgt_account_id, src_entity):
    matched = False
    if entity['entityType'] == 'APM_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == src_entity['name'] and \
       entity['language'] == src_entity['language']:
        matched = True
    return matched


def matched_mobile_app(entity, tgt_account_id, src_entity):
    matched = False
    if entity['entityType'] == 'MOBILE_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == src_entity['name']:
        matched = True
    return matched


def matched_apm_app_name(entity, tgt_account_id, name):
    matched = False
    if entity['entityType'] == 'APM_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == name:
        matched = True
    return matched


def matched_mobile_app_name(entity, tgt_account_id, name):
    matched = False
    if entity['entityType'] == 'MOBILE_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == name:
        matched = True
    return matched


def matched_synth_monitor_name(entity, tgt_account_id, name):
    matched = False
    if entity['entityType'] == 'SYNTHETIC_MONITOR_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == name:
        matched = True
    return matched


def matched_browser_app(entity, tgt_account_id, src_entity):
    matched = False
    if entity['entityType'] == 'BROWSER_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == src_entity['name']:
        matched = True
    return matched


def matched_browser_app_name(entity, tgt_account_id, name):
    matched = False
    if entity['entityType'] == 'BROWSER_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == name:
        matched = True
    return matched


def get_matching_kt(tgt_api_key, kt_name):
    filter_params = {'filter[name]': kt_name}
    result = {'entityFound': False}
    response = requests.get(GET_APM_KT_URL, headers=rest_api_headers(tgt_api_key), params=filter_params)
    result['status'] = response.status_code
    if response.text:
        response_json = response.json()
        if KEY_TRANSACTIONS in response_json:
            if len(response_json[KEY_TRANSACTIONS]) > 0:
                result['entityFound'] = True
                result['entity'] = response_json[KEY_TRANSACTIONS][0]
    return result


def extract_entities(gql_rsp_json):
    rsp_entities = gql_rsp_json['data']['actor']['entitySearch']['results']['entities']
    return list(filter(None, rsp_entities))  # remove empty dicts from list


def gql_get_matching_entity(api_key, entity_type, src_entity, tgt_account_id):
    logger.info('looking for matching entity ' + src_entity['name'] + ' in account ' + tgt_account_id)
    payload = search_query_payload(entity_type, src_entity['name'])
    result = {'entityFound': False}
    response = requests.post(GRAPHQL_URL, headers=gql_headers(api_key), data=json.dumps(payload))
    result['status'] = response.status_code
    if response.text:
        response_json = response.json()
        if 'errors' in response_json:
            if response.text:
                result['error'] = response_json['errors']
            logger.error(result)
        else:
            result['count'] = response_json['data']['actor']['entitySearch']['count']
            result['entities'] = extract_entities(response_json)
            if result['count'] > 0:
                set_matched_entity(result['entities'], entity_type, result, src_entity, tgt_account_id)
    else:
        logger.warn('No response for this query response received ' + str(response))
    logger.info('entity match result : ' + str(result))
    return result


def set_matched_entity(entities, entity_type, result, src_entity, tgt_account_id):
    for entity in entities:
        if entity_type == APM_APP and matched_apm_app(entity, tgt_account_id, src_entity):
            result['entityFound'] = True
            result['entity'] = entity
            break
        if entity_type == BROWSER_APP and matched_browser_app(entity, tgt_account_id, src_entity):
            result['entityFound'] = True
            result['entity'] = entity
            break
        if entity_type == MOBILE_APP and matched_mobile_app(entity, tgt_account_id, src_entity):
            result['entityFound'] = True
            result['entity'] = entity
            break


def gql_get_matching_entity_by_name(api_key, entity_type, name, tgt_acct_id):
    logger.info('Searching matching entity for type:' + entity_type + ', name:' + name + ', acct:' + tgt_acct_id)
    payload = search_query_payload(entity_type, name)
    result = {'entityFound': False}
    response = requests.post(GRAPHQL_URL, headers=gql_headers(api_key), data=json.dumps(payload))
    result['status'] = response.status_code
    if response.text:
        response_json = response.json()
        if 'errors' in response_json:
            if response.text:
                result['error'] = response_json['errors']
            logger.error(result)
        else:
            result['count'] = response_json['data']['actor']['entitySearch']['count']
            result['entities'] = extract_entities(response_json)
            if result['count'] > 0:
                set_matched_entity_by_name(tgt_acct_id, entity_type, name, result)
    else:
        logger.warn('No response for this query response received ' + str(response))
    logger.info('entity match result : ' + str(result))
    return result


def set_matched_entity_by_name(acct_id, entity_type, name, result):
    for entity in result['entities']:
        if entity_type == APM_APP and matched_apm_app_name(entity, acct_id, name):
            result['entityFound'] = True
            result['entity'] = entity
        if entity_type == BROWSER_APP and matched_browser_app_name(entity, acct_id, name):
            result['entityFound'] = True
            result['entity'] = entity
        if entity_type == MOBILE_APP and matched_mobile_app_name(entity, acct_id, name):
            result['entityFound'] = True
            result['entity'] = entity
        if entity_type == SYNTH_MONITOR and matched_synth_monitor_name(entity, acct_id, name):
            result['entityFound'] = True
            result['entity'] = entity


def show_url_for_app(entity_type, app_id):
    if MOBILE_APP == entity_type:
        show_url = SHOW_MOBILE_APP_URL
    if APM_APP == entity_type:
        show_url = SHOW_APM_APP_URL
    if show_url:
        return show_url + app_id + '.json'
    logger.error('Only supported for ' + MOBILE_APP + ' and ' + APM_APP)


def get_app_entity(api_key, entity_type, app_id):
    result = {'entityFound': False}
    get_url = show_url_for_app(entity_type, app_id)
    response = requests.get(get_url, headers=rest_api_headers(api_key))
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            logger.error("Error getting application info for app_id " + app_id)
            result['error'] = response.text
    else:
        result['entityFound'] = True
        result['entity'] = response.json()['application']
    return result


def get_apm_entity_by_name(api_key, app_name):
    params = {'filter[name]': app_name}
    result = {'entityFound': False}
    response = requests.get(GET_APM_APP_URL, headers=rest_api_headers(api_key), params=params)
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            logger.error("Error getting application info for app_name " + app_name)
            result['error'] = response.text
    else:
        if response.text:
            response_json = response.json()
            if 'applications' in response_json:
                for app in response_json['applications']:
                    if app['name'] == app_name:
                        result['entityFound'] = True
                        result['entity'] = app
    return result


def get_browser_entity(api_key, app_id):
    params = {'filter[ids]': [app_id]}
    result = {'entityFound': False}
    get_url = GET_BROWSER_APP_URL
    response = requests.get(get_url, headers=rest_api_headers(api_key), params=params)
    logger.info(response.url)
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            logger.error("Error getting application info for app_id " + app_id)
            result['error'] = response.text
    else:
        response_json = response.json()
        if 'browser_applications' in response_json.keys() and len(response_json['browser_applications']) == 1:
            result['entityFound'] = True
            result['entity'] = response_json['browser_applications'][0]
            # remove unnecessary key values just retaining id and name
            result['entity'].pop('browser_monitoring_key')
            result['entity'].pop('loader_script')
        else:
            logger.error("Did not find browser_applications in response for " + app_id)
    return result


def get_apm_kt(api_key, kt_id):
    result = {'entityFound': False}
    get_url = SHOW_APM_KT_URL + kt_id + '.json'
    response = requests.get(get_url, headers=rest_api_headers(api_key))
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            logger.error("Error getting application info for app_id " + kt_id)
            result['error'] = response.text
    else:
        result['entityFound'] = True
        result['entity'] = response.json()['key_transaction']
    return result


def get_entity(api_key, entity_type, entity_id):
    if entity_type in [APM_APP, MOBILE_APP]:
        return get_app_entity(api_key, entity_type, entity_id)
    if entity_type == BROWSER_APP:
        return get_browser_entity(api_key, entity_id)
    if entity_type == APM_KT:
        return get_apm_kt(api_key, entity_id)
    logger.warn('Skipping non APM entities ' + entity_type)
    return {'entityFound':  False}


# didn't end up using this as it was returning 500 errors sporadically in my test account
# see gql_mutate_add_tag instead
def put_apm_label(api_key, category, name, applications):
    label_payload = {'label': {'category': category, 'name': name, 'links': {'applications': applications}}}
    result = {}
    response = requests.put(PUT_LABEL_URL, headers=rest_api_headers(api_key), data=json.dumps(label_payload))
    result['status'] = response.status_code
    if response.status_code in [200, 204] and response.text:
        result['label'] = response.json()['label']
    elif response.text:
        result['error'] = response.text
    return result


def put_apm_settings(api_key, app_id, app_settings):
    logger.debug(app_settings)
    updated_settings = {
          "application": {
            "settings": {
              "app_apdex_threshold": str(app_settings['application']['settings']['app_apdex_threshold']),
              "end_user_apdex_threshold": str(app_settings['application']['settings']['end_user_apdex_threshold']),
              "enable_real_user_monitoring": str(app_settings['application']['settings']['enable_real_user_monitoring'])
            }
          }
        }
    result = {}
    update_app_url = SHOW_APM_APP_URL + str(app_id) + '.json'
    response = requests.put(update_app_url, headers=rest_api_headers(api_key), data=json.dumps(updated_settings))
    result['status'] = response.status_code
    if response.status_code in [200, 204] and response.text:
        result['application'] = response.json()['application']
    elif response.text:
        result['error'] = response.text
    return result


# input : key_values - dict with key and array of values as value
def tags_arr_from(arr_label_keys):
    tags_arr = []
    for label_key in arr_label_keys:
        label_parts = label_key.split(':')
        tag_key_values = {'key': label_parts[0], 'values': [label_parts[1]]}
        tags_arr.append(tag_key_values)
    return tags_arr


def mutate_tags_payload(entity_guid, arr_label_keys, mutate_action):
    apply_tags_query = '''mutation($entityGuid: EntityGuid!, $tags: [TaggingTagInput!]!) 
                            {''' + mutate_action + '''(guid: $entityGuid, tags: $tags) {
                                        errors { 
                                            message
                                            type 
                                        } 
                                    }
                          }'''
    arr_tags = tags_arr_from(arr_label_keys)
    variables = {'entityGuid': entity_guid, 'tags': arr_tags}
    payload = {'query': apply_tags_query, 'variables': variables}
    return payload


def apply_tags_payload(entity_guid, arr_label_keys):
    return mutate_tags_payload(entity_guid, arr_label_keys, 'taggingAddTagsToEntity')


def replace_tags_payload(entity_guid, arr_label_keys):
    return mutate_tags_payload(entity_guid, arr_label_keys, 'taggingReplaceTagsOnEntity')


def gql_mutate_add_tags(per_api_key, entity_guid, arr_label_keys):
    payload = apply_tags_payload(entity_guid, arr_label_keys)
    result = {}
    response = requests.post(GRAPHQL_URL, headers=gql_headers(per_api_key), data=json.dumps(payload))
    result['status'] = response.status_code
    if response.text:
        response_json = response.json()
        if 'errors' in response_json:
            logger.error('Error : ' + response.text)
            result['error'] = response_json['errors']
        else:
            logger.info('Success : ' + response.text)
            result['response'] = response_json
    return result


def gql_mutate_replace_tags(per_api_key, entity_guid, arr_label_keys):
    payload = replace_tags_payload(entity_guid, arr_label_keys)
    result = {}
    response = requests.post(GRAPHQL_URL, headers=gql_headers(per_api_key), data=json.dumps(payload))
    result['status'] = response.status_code
    if response.text:
        response_json = response.json()
        if 'errors' in response_json:
            logger.error('Error : ' + response.text)
            result['error'] = response_json['errors']
        else:
            logger.info('Success : ' + response.text)
            result['response'] = response_json
    return result


def get_dashboard_definition(api_key, name):
    params = {'filter[title]': name}
    result = {'entityFound': False, 'status': 404}
    results = utils.get_paginated_entities(api_key, GET_DASHBOARDS_URL, DASHBOARDS, params)
    if results['response_count'] <= 0:
        return result
    for dashboard in results[DASHBOARDS]:
        if dashboard['title'] == name:
            result['status'] = 200
            result['entityFound'] = True
            result['entity'] = dashboard
            break
    return result


def get_dashboard_widgets(api_key, dashboard_id):
    result = {'entityFound': False}
    db_id = str(dashboard_id)
    get_dashboard_url = SHOW_DASHBOARDS_URL + db_id + '.json'
    response = requests.get(get_dashboard_url, headers=rest_api_headers(api_key))
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            logger.error("Error getting dashboard " + db_id)
            result['error'] = response.text
    else:
        if response.text:
            response_json = response.json()
            if 'dashboard' in response_json:
                result['entityFound'] = True
                result['entity'] = response_json['dashboard']
    return result


def post_dashboard(api_key, dashboard):
    response = requests.post(GET_DASHBOARDS_URL, headers=rest_api_headers(api_key), data=json.dumps(dashboard))
    result = {'status': response.status_code}
    if response.status_code != 200:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating Dashboard" + dashboard['title'] + " : " +
                         str(response.status_code) + " : " + response.text)
    if response.status_code == 200 and response.text:
        result['entityCreated'] = True
        result['entity'] = response.json()
    return result


def delete_dashboard(api_key, dashboard_id):
    delete_url = DEL_DASHBOARDS_URL + str(dashboard_id) + '.json'
    result = requests.delete(delete_url, headers=rest_api_headers(api_key))
    logger.info(result.url + ' : ' + str(result.status_code))
    return result


def delete_dashboards(api_key, dashboard_names):
    for dashboard_name in dashboard_names:
        result = get_dashboard_definition(api_key, dashboard_name)
        if result['entityFound']:
            delete_dashboard(api_key, result['entity']['id'])


def delete_all_dashboards(api_key):
    result = utils.get_paginated_entities(api_key, GET_DASHBOARDS_URL, 'dashboards')
    for dashboard in result['dashboards']:
        logger.info('Deleting ' + dashboard['title'])
        delete_dashboard(api_key, dashboard['id'])
