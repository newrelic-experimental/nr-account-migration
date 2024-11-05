import json
import requests
import os
import library.utils as utils
import library.monitortypes as monitortypes
import library.status.monitorstatus as monitorstatus
import library.migrationlogger as nrlogger
import library.clients.gql as nerdgraph
from library.clients.endpoints import Endpoints
import time


# monitors provides a mix of REST and GraphQL client calls for fetching a monitor and a monitor script
# and populating a monitor_json with it's script

logger = nrlogger.get_logger(os.path.basename(__file__))
NEW_MONITOR_ID = 'new_monitor_id'
MON_SEC_CREDENTIALS = 'secureCredentials'


class MonitorsClient:

    def __init__(self):
        pass


    @staticmethod
    def setup_headers(api_key):
        return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


    @staticmethod
    def query_monitors_gql(cursor):
        query = '''query($cursor: String) {
            actor {
                entitySearch(query: "domain = 'SYNTH' AND type = 'MONITOR'") {
                    results (cursor: $cursor) {
                        entities {
                            ... on SyntheticMonitorEntityOutline {
                                accountId
                                guid
                                monitorType
                                monitorSummary {
                                    status
                                }
                                name
                                period
                                tags {
                                    key
                                    values
                                }
                                monitorId
                                monitoredUrl
                              }
                        }
                        nextCursor
                    }
                }
            }
        }'''        
        variables = {'cursor': cursor}
        return {'query': query, 'variables': variables}


    @staticmethod
    def fetch_all_monitors(api_key, account_id, region):
        all_monitors_def_json = []
        done = False
        cursor = None
        while not done:
            try:
                logger.info(f'Querying monitors for account {account_id}')
                payload = MonitorsClient.query_monitors_gql(cursor)
                logger.debug(json.dumps(payload))
                result = nerdgraph.GraphQl.post(api_key, payload, region)
                logger.debug(json.dumps(result))
                if ('error' in result):
                    logger.error(f'Could not fetch monitors')
                    logger.error(result['error'])
                    break
                else:
                  # No error attribute for monitors
                  if 'response' in result:
                    cursor = result['response']['data']['actor']['entitySearch']['results']['nextCursor']
                    all_monitors_def_json = all_monitors_def_json + result['response']['data']['actor']['entitySearch']['results']['entities']
                    # Filter only synthetics monitors that match the account_id using list comprehension
                    all_monitors_def_json = [monitor for monitor in all_monitors_def_json if monitor['accountId'] == int(account_id)]
                    logger.info("Fetched monitor definitions : " + str(len(all_monitors_def_json)))
                  else:
                    logger.error(f'Could not fetch monitors')
                    logger.error(result)
                    break
                if cursor is None:
                    done = True
            except Exception as e:
                logger.error(f'Error querying monitors for account {account_id}')
                logger.error(e)
                done = True
        return all_monitors_def_json


    @staticmethod
    def query_monitor_gql(entity_guid):
        query = '''query($entityGuid: EntityGuid!) {
            actor {
                entities(guids: [$entityGuid]) {
                    ... on SyntheticMonitorEntity {
                        guid
                        name
                        accountId
                        monitorType
                        monitorSummary {
                            status
                        }
                        period
                        tags {
                            key
                            values
                        }
                        monitorId
                        monitoredUrl
                    }
                }
            }
        }'''
        variables = {'entityGuid': entity_guid}
        return {'query': query, 'variables': variables}


    @staticmethod
    def fetch_monitor(api_key, monitor_name, monitor_guid, region):
        monitor = None
        try:
            payload = MonitorsClient.query_monitor_gql(monitor_guid)
            logger.debug(json.dumps(payload))
            result = nerdgraph.GraphQl.post(api_key, payload, region)
            logger.debug(json.dumps(result))
            if ('error' in result):
                logger.error(f'Could not fetch monitor {monitor_name}')
                logger.error(result['error'])
            else:
                # No error attribute for script
                if 'response' in result:
                    logger.info("got script for " + monitor_name)
                    monitor = result['response']['data']['actor']['entities'][0]
                else:
                    logger.error(f'Could not fetch script')
                    logger.error(result)
        except Exception as e:
            logger.error(f'Error querying {monitor_name} monitor with entity_guid {monitor_guid}')
            logger.error(e)
        logger.debug(f"Fetched monitor {monitor_name}")
        return monitor



    @staticmethod
    def get_monitor(api_key, monitor_id, region=Endpoints.REGION_US):
        get_monitor_url = Endpoints.of(region).MONITORS_URL + monitor_id
        response = requests.get(get_monitor_url, headers=MonitorsClient.setup_headers(api_key))
        result = {'status': response.status_code }
        if response.status_code == 200:
            result['monitor'] = response.json()
        else:
            logger.error('Error fetching monitor ' + monitor_id)
            if response.text:
                logger.error('Error message : ' + response.text)
                result['error'] = response.text
        return result


    @staticmethod
    def query_script_gql(account_id, entity_guid):
        query = '''query($accountId: Int!, $entityGuid: EntityGuid!) {
            actor {
                account(id: $accountId) {
                    synthetics {
                        script(monitorGuid: $entityGuid) {
                            text
                        }
                    }
                }
            }
        }'''        
        variables = {'accountId': int(account_id), 'entityGuid': entity_guid}
        return {'query': query, 'variables': variables}


    @staticmethod
    def fetch_script(api_key, account_id, monitor_name, entity_guid, region):
        script_text = None
        try:
            payload = MonitorsClient.query_script_gql(account_id, entity_guid)
            logger.debug(json.dumps(payload))
            result = nerdgraph.GraphQl.post(api_key, payload, region)
            logger.debug(json.dumps(result))
            if ('error' in result):
                logger.error(f'Could not fetch script')
                logger.error(result['error'])
            else:
                # No error attribute for script
                if 'response' in result:
                    logger.info("got script for " + monitor_name)
                    script_text = result['response']['data']['actor']['account']['synthetics']['script']['text']
                else:
                    logger.error(f'Could not fetch script')
                    logger.error(result)
        except Exception as e:
            logger.error(f'Error querying {monitor_name} script for account {account_id} with entity_guid {entity_guid}')
            logger.error(e)
        logger.debug("Fetched script : " + script_text)
        return script_text


    @staticmethod
    def populate_script(api_key, account_id, monitor_json, entity_guid, region):
        monitor_name = monitor_json['definition']['name']
        logger.info(f'Querying {monitor_name} script for account {account_id}, with entity_guid {entity_guid}')
        script_text = MonitorsClient.fetch_script(api_key, account_id, monitor_name, entity_guid, region)
        # TODO: Check if script_text is None?
        # TODO: base64 encode script_text?
        monitor_json['script'] = script_text


    @staticmethod
    def create_simple_monitor_gql(account_id, monitor):
        # Create syntheticsCreateSimpleMonitor
        mutation = '''mutation ($accountId: Int!, $monitor: SyntheticsCreateSimpleMonitorInput!) {
            syntheticsCreateSimpleMonitor(
                accountId: $accountId
                monitor: $monitor
            ) {
                monitor {
                    guid
                }
                errors {
                    description
                    type
                }
            }
        }'''
        variables = {'accountId': int(account_id), 'monitor': monitor}
        return {'query': mutation, 'variables': variables}


    @staticmethod
    def create_script_api_monitor_gql(account_id, monitor):
        # Create syntheticsCreateScriptApiMonitor
        mutation = '''mutation ($accountId: Int!, $monitor: SyntheticsCreateScriptApiMonitorInput!) {
            syntheticsCreateScriptApiMonitor(
                accountId: $accountId
                monitor: $monitor
            ) {
                monitor {
                    guid
                }
                errors {
                    description
                    type
                }
            }
        }'''
        variables = {'accountId': int(account_id), 'monitor': monitor}
        return {'query': mutation, 'variables': variables}


    @staticmethod
    def create_simple_browser_monitor_gql(account_id, monitor):
        # Create syntheticsCreateSimpleBrowserMonitor
        mutation = '''mutation ($accountId: Int!, $monitor: SyntheticsCreateSimpleBrowserMonitorInput!) {
            syntheticsCreateSimpleBrowserMonitor(
                accountId: $accountId
                monitor: $monitor
            ) {
                monitor {
                    guid
                }
                errors {
                    description
                    type
                }
            }
        }'''
        variables = {'accountId': int(account_id), 'monitor': monitor}
        return {'query': mutation, 'variables': variables}


    @staticmethod
    def create_script_browser_monitor_gql(account_id, monitor):
        # Create syntheticsCreateScriptBrowserMonitor
        mutation = '''mutation ($accountId: Int!, $monitor: SyntheticsCreateScriptBrowserMonitorInput!) {
            syntheticsCreateScriptBrowserMonitor(
                accountId: $accountId
                monitor: $monitor
            ) {
                monitor {
                    guid
                }
                errors {
                    description
                    type
                }
            }
        }'''
        variables = {'accountId': int(account_id), 'monitor': monitor}
        return {'query': mutation, 'variables': variables}


    @staticmethod
    def post_monitor_definition(api_key, monitor_name, monitor, monitor_status, tgt_acct_id, region=Endpoints.REGION_US):
        guid = None
        monitor_data = monitortypes.prep_monitor_type(monitor)
        logger.debug(monitor_data)
        payload = None
        try:
            if monitor['definition']['monitorType'] == 'SIMPLE':
                payload = MonitorsClient.create_simple_monitor_gql(tgt_acct_id, monitor_data)
            elif monitor['definition']['monitorType'] == 'SCRIPT_API':
                payload = MonitorsClient.create_script_api_monitor_gql(tgt_acct_id, monitor_data)
            elif monitor['definition']['monitorType'] == 'BROWSER':
                payload = MonitorsClient.create_simple_browser_monitor_gql(tgt_acct_id, monitor_data)
            elif monitor['definition']['monitorType'] == 'SCRIPT_BROWSER':
                payload = MonitorsClient.create_script_browser_monitor_gql(tgt_acct_id, monitor_data)
            logger.debug(json.dumps(payload))
            result = nerdgraph.GraphQl.post(api_key, payload, region)
            post_status = {monitorstatus.STATUS: result['status']}
            logger.debug(json.dumps(result))
            # if result dict contains 'error' key, then it's an error
            if 'error' in result:
                post_status[monitorstatus.ERROR] = result['error']
                logger.error(f'Error creating monitor {monitor_name}')
                logger.error(result['error'])
            if monitor['definition']['monitorType'] == 'SIMPLE':
                if result['response']['data']['syntheticsCreateSimpleMonitor']['errors']:
                    post_status[monitorstatus.ERROR] = result['response']['data']['syntheticsCreateSimpleMonitor']['errors']
                    logger.error(f'Could not create monitor {monitor_name}')
                    logger.error(result['response']['data']['syntheticsCreateSimpleMonitor']['errors'])
                else:
                    guid = result['response']['data']['syntheticsCreateSimpleMonitor']['monitor']['guid']
            elif monitor['definition']['monitorType'] == 'SCRIPT_API':
                if result['response']['data']['syntheticsCreateScriptApiMonitor']['errors']:
                    post_status[monitorstatus.ERROR] = result['response']['data']['syntheticsCreateScriptApiMonitor']['errors']
                    logger.error(f'Could not create monitor {monitor_name}')
                    logger.error(result['response']['data']['syntheticsCreateScriptApiMonitor']['errors'])
                else:
                    guid = result['response']['data']['syntheticsCreateScriptApiMonitor']['monitor']['guid']
            elif monitor['definition']['monitorType'] == 'BROWSER':
                if result['response']['data']['syntheticsCreateSimpleBrowserMonitor']['errors']:                
                    post_status[monitorstatus.ERROR] = result['response']['data']['syntheticsCreateSimpleBrowserMonitor']['errors']
                    logger.error(f'Could not create monitor {monitor_name}')
                    logger.error(result['response']['data']['syntheticsCreateSimpleBrowserMonitor']['errors'])
                else:
                    guid = result['response']['data']['syntheticsCreateSimpleBrowserMonitor']['monitor']['guid']
            elif monitor['definition']['monitorType'] == 'SCRIPT_BROWSER':
                if result['response']['data']['syntheticsCreateScriptBrowserMonitor']['errors']:                
                    post_status[monitorstatus.ERROR] = result['response']['data']['syntheticsCreateScriptBrowserMonitor']['errors']
                    logger.error(f'Could not create monitor {monitor_name}')
                    logger.error(result['response']['data']['syntheticsCreateScriptBrowserMonitor']['errors'])
                else:
                    guid = result['response']['data']['syntheticsCreateScriptBrowserMonitor']['monitor']['guid']
        except Exception as e:
            logger.error(f'Error creating {monitor_name} script for account {tgt_acct_id}')
            logger.error(e)
            post_status[monitorstatus.ERROR] = e
        if guid is not None:
            post_status[NEW_MONITOR_ID] = guid
            logger.info(f"Monitor {monitor_name} created with guid: {guid}")
        monitor_status[monitor_name] = post_status
        return guid


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


def update(api_key, monitor_id, update_json, monitor_name, region=Endpoints.REGION_US):
    logger.info('Updating ' + monitor_name)
    update_payload = json.dumps(update_json)
    logger.info(update_payload)
    put_monitor_url = Endpoints.of(region).MONITORS_URL + str(monitor_id)
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


def delete_monitor(monitor, target_acct, failure_status, success_status, tgt_api_key, region):
    logger.info(monitor)
    monitor_id = monitor['monitorId']
    monitor_name = monitor['name']
    response = requests.delete(Endpoints.of(region).MONITORS_URL + monitor_id,
                               headers=MonitorsClient.setup_headers(tgt_api_key))
    if response.status_code == 204:
        success_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
        logger.info(target_acct + ":" + monitor_name + ":" + str(success_status[monitor_name]))
    else:
        failure_status[monitor_name] = {'status': response.status_code, 'responseText': response.text}
        logger.info(target_acct + ":" + monitor_name + ":" + str(failure_status[monitor_name]))
    # trying to stay within 3 requests per second
    time.sleep(0.3)