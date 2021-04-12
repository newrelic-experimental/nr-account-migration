import requests
import json
import os
import library.migrationlogger as m_logger
import library.utils as utils
import collections

APM_APP = 'APM_APP'
APM_KT = 'APM_KT'
BROWSER_APP = 'BROWSER_APP'
APM_EXT_SVC = 'APM_EXT_SVC'
MOBILE_APP = 'MOBILE_APP'
SYNTH_MONITOR = 'SYNTH_MONITOR'
SYNTH_SECURE_CRED = 'SYNTH_SECURE_CRED'
DASHBOARD = 'DASHBOARD'
INFRA_HOST = 'INFRA_HOST'
INFRA_INT = 'INFRA_INT'
INFRA_LAMBDA = 'INFRA_LAMBDA'

# Mapping to entityType tag values
ent_type_lookup = {}
ent_type_lookup[APM_APP] = 'APM_APPLICATION_ENTITY'
ent_type_lookup[BROWSER_APP] = 'BROWSER_APPLICATION_ENTITY'
ent_type_lookup[MOBILE_APP] = 'MOBILE_APPLICATION_ENTITY'
ent_type_lookup[SYNTH_MONITOR] = 'SYNTHETIC_MONITOR_ENTITY'
ent_type_lookup[SYNTH_SECURE_CRED] = 'SECURE_CREDENTIAL_ENTITY'
ent_type_lookup[DASHBOARD] = 'DASHBOARD_ENTITY'
ent_type_lookup[INFRA_HOST] = 'INFRASTRUCTURE_HOST_ENTITY'
ent_type_lookup[INFRA_INT] = 'GENERIC_INFRASTRUCTURE_ENTITY'
ent_type_lookup[INFRA_LAMBDA] = 'INFRASTRUCTURE_AWS_LAMBDA_FUNCTION_ENTITY'


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
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


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
                        tags {
                            key
                            values
                        }
                    } '''
    if entity_type == BROWSER_APP:
        return ''' ... on BrowserApplicationEntityOutline {
                                guid
                                applicationId
                                name
                                accountId
                                type
                                entityType
                                tags {
                                    key
                                    values
                                }
                            } '''
    if entity_type == MOBILE_APP:
        return ''' ... on MobileApplicationEntityOutline {
                        guid
                        applicationId
                        name
                        accountId
                        type                        
                        entityType
                        tags {
                            key
                            values
                        }
                    } '''
    if entity_type == SYNTH_MONITOR:
        return ''' ... on SyntheticMonitorEntityOutline {
                            guid
                            entityType
                            accountId
                            monitorId
                            name                            
                            monitorType
                            tags {
                                key
                                values
                            } 
                        }  '''
    if entity_type == SYNTH_SECURE_CRED:
        return ''' ... on SecureCredentialEntityOutline {
                            guid
                            entityType
                            accountId
                            name                            
                            secureCredentialId
                            tags {
                                key
                                values
                            } 
                        }  '''
    if entity_type == DASHBOARD:
        return ''' ... on DashboardEntityOutline {
                  guid
                  name
                  accountId
                  type
                  entityType
                    tags {
                        key
                        values
                    }
                } '''
    if entity_type == INFRA_HOST:
        return ''' ... on InfrastructureHostEntityOutline {
                guid
                name
                accountId
                type
                entityType
                tags {
                    key
                    values
                }
            } '''
    if entity_type == INFRA_INT:
        return ''' ... on GenericInfrastructureEntityOutline {
                guid
                name
                accountId
                type
                entityType
                tags {
                    key
                    values
                }
            } '''
    if entity_type == INFRA_LAMBDA: 
        return ''' ... on InfrastructureAwsLambdaFunctionEntityOutline {
                guid
                name
                accountId
                type
                entityType
                runtime
                tags {
                    key
                    values
                }
            } '''


def search_query_payload(entity_type, entity_name, acct_id = None):
    gql_search_type = 'APPLICATION'
    if entity_type == SYNTH_MONITOR:
        gql_search_type = 'MONITOR'
    elif entity_type == DASHBOARD:
        gql_search_type = 'DASHBOARD'
    elif entity_type == SYNTH_SECURE_CRED:
        gql_search_type = 'SECURE_CRED'
    elif entity_type == INFRA_HOST:
        gql_search_type = 'HOST'
    elif entity_type == INFRA_LAMBDA:
        gql_search_type = 'AWSLAMBDAFUNCTION'
    # 
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
    if entity_type == INFRA_INT:
        # entityType cannot be used in a search
        # Integrations use a large number of types, making maintaining separate queries unmaintainable
        matching_condition = "name = '" + entity_name + "' AND domain = 'INFRA' AND type != 'HOST' AND type != 'AWSLAMBDAFUNCTION'"
    else:
        matching_condition = "name = '" + entity_name + "' AND type = '"+gql_search_type+"'"
    if acct_id != None:
        matching_condition += " AND tags.accountId = '" + str(acct_id) + "'"
    variables = {'matchingCondition': matching_condition}
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



def matched_browser_app(entity, tgt_account_id, src_entity):
    matched = False
    if entity['entityType'] == 'BROWSER_APPLICATION_ENTITY' and \
       str(entity['accountId']) == str(tgt_account_id) and \
       entity['name'] == src_entity['name']:
        matched = True
    return matched



def matched_entity_name(entity_type, entity, tgt_account_id, name):
    matched = False
    if entity['entityType'] == ent_type_lookup[entity_type] and \
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
    payload = search_query_payload(entity_type, src_entity['name'], tgt_account_id)
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
    logger.info('Searching matching entity for type:' + entity_type + ', name:' + name + ', acct:' + str(tgt_acct_id))
    payload = search_query_payload(entity_type, name, tgt_acct_id)
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
        if matched_entity_name(entity_type, entity, acct_id, name):
            result['entityFound'] = True
            result['entity'] = entity
            break

def get_entities_payload(entity_type, acct_id = None, nextCursor = None):
    gql_search_type = 'APPLICATION'
    if entity_type == SYNTH_MONITOR:
        gql_search_type = 'MONITOR'
    elif entity_type == DASHBOARD:
        gql_search_type = 'DASHBOARD'

    entity_search_query = '''query($matchingCondition: String!) { 
                                    actor { 
                                        entitySearch(query: $matchingCondition) {
                                            count
                                            results''' + ('' if not nextCursor else '(cursor: "' + nextCursor + '")') + ''' {
                                                entities { ''' + entity_outline(entity_type) + '''
                                                }
                                                nextCursor
                                            } 
                                        } 
                                    } 
                                }
                                '''
    matching_condition = "type = '"+gql_search_type+"'"
    if acct_id != None:
        matching_condition += " AND tags.accountId = '" + str(acct_id) + "'"
    variables = {'matchingCondition': matching_condition}
    payload = {'query': entity_search_query, 'variables': variables}
    return payload

def gql_get_entities_by_type(api_key, entity_type, acct_id = None):
    logger.info('Searching for entities by type:' + entity_type + ', acct:' + str(acct_id))

    done = False
    nextCursor = None
    count = 0
    result = {}
    error = None
    entities = []

    while not done:
        payload = get_entities_payload(entity_type, acct_id, nextCursor)

        response = requests.post(GRAPHQL_URL, headers=gql_headers(api_key), data=json.dumps(payload))
        if response.status_code != 200:
            done = True
            if response.text:
                error = response.text
                logger.error("Error fetching entities : " +
                            str(response.status_code) + " : " + response.text)
            break

        if not response.text:
            done = True
            break

        response_json = response.json()
        if 'errors' in response_json:
            done = True
            logger.error('Error : ' + response.text)
            error = response_json['errors']
            break

        entitySearch = response_json['data']['actor']['entitySearch']
        count = int(entitySearch['count'])
        nextCursor = entitySearch['results']['nextCursor']

        if 'entities' in entitySearch['results']:
            for entity in entitySearch['results']['entities']:
                entities.append(entity)

        if not nextCursor:
            done = True
            break

    if error != None:
        result['error'] = error
    else:
        result['count'] = count
        result['entities'] = entities

    return result

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

# Input: tags from source and target entities
# Output: array of tags that need to be applied on target entity
def tags_diff(src_tags, tgt_tags):
    tags_arr = []
    for src_tag in src_tags:
        match_found = False
        for tgt_tag in tgt_tags:
            if src_tag['key'] == tgt_tag['key']:
                match_found = True
                continue
        if match_found == False:
            tags_arr.append(src_tag)
    return tags_arr

def mutate_tags_payload(entity_guid, arr_tags, mutate_action):
    apply_tags_query = '''mutation($entityGuid: EntityGuid!, $tags: [TaggingTagInput!]!) 
                            {''' + mutate_action + '''(guid: $entityGuid, tags: $tags) {
                                        errors { 
                                            message
                                            type 
                                        } 
                                    }
                          }'''
    variables = {'entityGuid': entity_guid, 'tags': arr_tags}
    payload = {'query': apply_tags_query, 'variables': variables}
    return payload


def apply_tags_payload(entity_guid, arr_tags):
    return mutate_tags_payload(entity_guid, arr_tags, 'taggingAddTagsToEntity')


def replace_tags_payload(entity_guid, arr_tags):
    return mutate_tags_payload(entity_guid, arr_tags, 'taggingReplaceTagsOnEntity')


def gql_mutate_add_tags(per_api_key, entity_guid, arr_tags):
    payload = apply_tags_payload(entity_guid, arr_tags)
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


def gql_mutate_replace_tags(per_api_key, entity_guid, tags):
    payload = replace_tags_payload(entity_guid, tags)
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


def get_dashboard_definition(per_api_key, name, acct_id):
    result = gql_get_matching_entity_by_name(per_api_key, DASHBOARD, name, acct_id)
    if not result['entityFound']:
        return None

    return result['entity']

def dashboard_query_payload(dashboard_guid):
    dashboard_query = '''query ($guid: EntityGuid!)
                    {
                        actor {
                            entity(guid: $guid) {
                                guid
                                ... on DashboardEntity {
                                name
                                permissions
                                    pages {
                                        name
                                        widgets {
                                            visualization { id }
                                            title
                                            layout { row width height column }
                                            rawConfiguration
                                        }
                                    }
                                }
                            }
                        }
                    }
                    '''
    variables = {'guid': dashboard_guid}
    payload = {'query': dashboard_query, 'variables': variables}
    return payload

def get_dashboard_widgets(per_api_key, dashboard_guid):
    result = {'entityFound': False}
    payload = dashboard_query_payload(dashboard_guid)
    response = requests.post(GRAPHQL_URL, headers=gql_headers(per_api_key), data=json.dumps(payload))
    result['status'] = response.status_code
    if response.status_code != 200:
        if response.text:
            result['error'] = response.text
            logger.error("Error fetching dashboard with guid " + dashboard_guid + " : " +
                            str(response.status_code) + " : " + response.text)

    if response.status_code == 200 and response.text:
        response_json = response.json()
        if 'errors' in response_json:
            if response.text:
                result['error'] = response_json['errors']
            logger.error(result)
        else:
            result['entityFound'] = True
            result['entity'] = response_json['data']['actor']['entity']
    else:
        logger.warn('No response for this query response received ' + str(response))
    logger.info('entity match result : ' + str(result))
    return result


def create_dashboard_payload(acct_id, dashboard):
    create_dashboard_query = '''mutation create($accountId: Int!, $dashboard: Input!) {
          dashboardCreate(accountId: $accountId, dashboard: $dashboard) {
            entityResult {
              guid
              name
            }
            errors {
              description
            }
          }
        }'''
    variables = {'accountId': acct_id, 'dashboard': dashboard}
    payload = {'query': create_dashboard_query, 'variables': variables}
    return payload

def post_dashboard(per_api_key, dashboard, acct_id):
    payload = create_dashboard_payload(acct_id, dashboard)
    response = requests.post(GRAPHQL_URL, headers=gql_headers(per_api_key), data=json.dumps(payload))
    result = {'status': response.status_code}

    if response.status_code != 200 and response.status_code != 201:
        if response.text:
            result['error'] = response.text
            logger.error("Error creating Dashboard" + dashboard['name'] + " : " +
                         str(response.status_code) + " : " + response.text)

    if (response.status_code == 200 or response.status_code == 201) and response.text:
        response_json = response.json()
        if 'errors' in response_json:
            logger.error('Error : ' + response.text)
            result['error'] = response_json['errors']
        else:
            dashboard_create = response_json['data']['dashboardCreate']
            if 'errors' in dashboard_create and isinstance(dashboard_create['errors'], collections.Sequence):
                logger.error('Error : ' + response.text)
                result['error'] = dashboard_create['errors']
            else:
                logger.info('Success : ' + response.text)
                result['entityCreated'] = True
                result['entity'] = response_json['data']['dashboardCreate']['entityResult']
    
    return result

def delete_dashboard_payload(guid):
    delete_dashboard_query = '''mutation delete($guid: EntityGuid!) {
                    dashboardDelete(guid: $guid) {
                            errors {
                                description
                            }
                            status
                        }
                    }'''
    variables = {'guid': guid}
    payload = {'query': delete_dashboard_query, 'variables': variables}
    return payload

def delete_dashboard(per_api_key, guid):
    payload = delete_dashboard_payload(guid)
    response = requests.post(GRAPHQL_URL, headers=gql_headers(per_api_key), data=json.dumps(payload))
    result = {'status': response.status_code}

    if response.status_code != 200:
        if response.text:
            result['error'] = response.text
            logger.error("Error delete dashboard with guid " + guid + " : " +
                         str(response.status_code) + " : " + response.text)

    if response.status_code == 200 and response.text:
        response_json = response.json()
        if 'errors' in response_json:
            logger.error('Error : ' + response.text)
            result['error'] = response_json['errors']
        else:
            dashboard_delete = response_json['data']['dashboardDelete']
            if 'errors' in dashboard_delete and isinstance(dashboard_delete['errors'], collections.Sequence):
                logger.error('Error : ' + response.text)
                result['error'] = dashboard_delete['errors']
            else:
                logger.info('Success : ' + response.text)
                result['entityDeleted'] = True
    
    return result

def delete_dashboards(per_api_key, dashboard_names, acct_id):
    for dashboard_name in dashboard_names:
        result = get_dashboard_definition(per_api_key, dashboard_name, acct_id)
        if result != None:
            delete_dashboard(per_api_key, result['guid'])


def delete_all_dashboards(per_api_key, acct_id):
    result = gql_get_entities_by_type(per_api_key, DASHBOARD, acct_id)
    if 'error' in result:
        logger.error('Error : ' + result['error'])
        return

    count = result['count']

    if count <= 0:
        logger.info('No dashboards to delete')
        return

    logger.info('Deleting ' + str(count) + ' dashboards')

    for dashboard in result['entities']:
        logger.info('Deleting ' + dashboard['name'])
        delete_dashboard(per_api_key, dashboard['guid'])
