import json
import requests
import os
import time
import library.migrationlogger as m_logger
import library.monitortypes as monitortypes
import library.status.monitorstatus as monitorstatus
import library.securecredentials as securecredentials
import library.clients.entityclient as ec


# monitors provides REST client calls for fetching a monitor and a monitor script
# and populating a monitor_json with it's script
# Batch size for fetching monitors, must be less than or equal to 100
BATCH_SIZE = 100
monitors_url = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/'
monitor_label_url = 'https://synthetics.newrelic.com/synthetics/api/v4/monitors/'
logger = m_logger.get_logger(os.path.basename(__file__))
NEW_MONITOR_ID = 'new_monitor_id'
MON_SEC_CREDENTIALS = 'secureCredentials'


def setup_headers(api_key):
    return {'X-Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def fetch_script(api_key, monitor_id):
    get_script_url = monitors_url + monitor_id + "/script"
    response = requests.get(get_script_url, headers=setup_headers(api_key))
    if response.status_code == 200:
        body_str = json.loads(response.text)
    else:
        body_str = ""
    return {'status': response.status_code, 'body': body_str}


def get_monitor(api_key, monitor_id):
    get_monitor_url = monitors_url + monitor_id
    response = requests.get(get_monitor_url, headers=setup_headers(api_key))
    result = {'status': response.status_code }
    if response.status_code == 200:
        result['monitor'] = response.json()
    else:
        logger.error('Error fetching monitor ' + monitor_id)
        if response.text:
            logger.error('Error message : ' + response.text)
            result['error'] = response.text
    return result


def fetch_all_monitors(api_key):
    query_params = {'offset': 0, 'limit': BATCH_SIZE}
    fetch_more = True
    all_monitors_def_json = []
    logger.info("Fetching all monitor definitions with query_params " + str(query_params))
    while fetch_more:
        response = requests.get(monitors_url, headers=setup_headers(api_key), params=query_params)
        response_json = json.loads(response.text)
        monitors_returned = response_json['count']
        if monitors_returned == 0 or monitors_returned < query_params['limit']:
            fetch_more = False
        query_params['offset'] = query_params['offset'] + monitors_returned
        all_monitors_def_json = all_monitors_def_json + response_json['monitors']
    logger.info("Fetched monitor definitions : " + str(len(all_monitors_def_json)))
    return all_monitors_def_json


def fetch_secure_credentials(insights_query_key, account_id, scripted_monitors, monitor_status):
    secure_credentials = set()
    for monitor_json in scripted_monitors:
        monitor_name = monitor_json['definition']['name']
        credentials_and_checks = securecredentials.from_insights(insights_query_key, account_id, monitor_name)
        monitor_status.update(credentials_and_checks)
        monitor_json.update(credentials_and_checks)
        if credentials_and_checks[monitorstatus.CHECK_COUNT] > 0:
            secure_credentials.union(credentials_and_checks[monitorstatus.SEC_CREDENTIALS])
    return secure_credentials


def populate_script(api_key, monitor_json, monitor_id):
    script_response = fetch_script(api_key, monitor_id)
    monitor_name = monitor_json['definition']['name']
    if script_response['status'] == 200:
        logger.info("got script for " + monitor_name)
        monitor_json['script'] = script_response['body']
    else:
        logger.error("Error fetching script for " + monitor_name + " code " + str(script_response['status']) +
                     " message " + json.dumps(script_response['body']))


def put_script(api_key, monitor_json, monitor_name, monitor_status):
    script_payload = json.dumps(monitor_json['script'])
    if 'location' in monitor_status[monitor_name]:
        script_url = monitor_status[monitor_name]['location'] + "/script"
        script_response = requests.put(script_url, headers=setup_headers(api_key), data=script_payload)
        monitor_status[monitor_name][monitorstatus.SCRIPT_STATUS] = script_response.status_code
        monitor_status[monitor_name][monitorstatus.SCRIPT_MESSAGE] = script_response.text
    else:
        logger.warn("No location found in monitor_status. Most likely it did not get created")
        monitor_status[monitor_name][monitorstatus.SCRIPT_STATUS] = -1
        monitor_status[monitor_name][monitorstatus.SCRIPT_MESSAGE] = 'MonitorNotFound'
    logger.info(monitor_status[monitor_name])


def get_target_monitor_guid(monitor_name, per_api_key, tgt_acct_id):
    result = ec.gql_get_matching_entity_by_name(per_api_key, ec.SYNTH_MONITOR, monitor_name, tgt_acct_id)
    monitor_guid = ''
    if not result['entityFound']:
        logger.warn('No matching entity found in target account ' + monitor_name)
    else:
        monitor_guid = result['entity']['guid']
    return monitor_guid


def apply_tags(tgt_acct_id, per_api_key, monitor_labels, monitor_name, monitor_status):
    if monitor_status[monitor_name]['status'] != 201:
        logger.warn('Skipping labels as monitor creation status is not 201')
        return
    monitor_guid = get_target_monitor_guid(monitor_name, per_api_key, tgt_acct_id)
    if not monitor_guid:
        logger.warn('No matching entity found trying again ' + monitor_name)
        time.sleep(0.5)
        monitor_guid = get_target_monitor_guid(monitor_name, per_api_key, tgt_acct_id)
    if not monitor_guid:
        logger.warn('No matching entity found in second attempt. Try increasing above sleep to a second or two')
    else:
        logger.info('Adding labels as tags')
        result = ec.gql_mutate_add_tags(per_api_key, monitor_guid, monitor_labels)
        if 'error' not in result:
            monitor_status[monitor_name][monitorstatus.LABELS] = [monitor_labels]
        else:
            monitor_status[monitor_name][monitorstatus.LABELS] = [result['error']]


def post_monitor_definition(api_key, monitor_name, monitor, monitor_status):
    prep_monitor = monitortypes.prep_monitor_type(monitor['definition'])
    monitor_json_str = json.dumps(prep_monitor)
    logger.debug(monitor_json_str)
    response = requests.post(monitors_url, headers=setup_headers(api_key), data=monitor_json_str)
    post_status = {monitorstatus.STATUS: response.status_code}
    logger.debug(response.headers)
    if response.status_code == 201:
        post_status[monitorstatus.LOCATION] = response.headers['Location']
        post_status[NEW_MONITOR_ID] = response.headers['Location'].split("/")[-1]
        logger.info(str(post_status))
    else:
        post_status[monitorstatus.ERROR] = response.text
        logger.error('Error creating monitor ' + monitor_name + ':' + str(post_status))
    monitor_status[monitor_name] = post_status
    logger.info(monitor_name + " : " + str(post_status))


def update(api_key, monitor_id, update_json, monitor_name):
    logger.info('Updating ' + monitor_name)
    update_payload = json.dumps(update_json)
    logger.info(update_payload)
    put_monitor_url = monitors_url + str(monitor_id)
    result = {'entityUpdated': False}
    response = requests.patch(put_monitor_url, headers=setup_headers(api_key), data=update_payload)
    result['status'] = response.status_code
    # A successful request will return a 204 No Content response, with an empty body.
    if response.status_code != 204:
        logger.error("Error updating monitor " + monitor_name + " : " + update_payload)
        if response.text:
            logger.error(response.text)
            result['error'] = response.txt
    else:
        result['updatedEntity'] = str(update_json)
    return result
