import base64
import os
import requests
import json
import library.clients.insightsclient as insightsclient
from library.status.monitorstatus import SEC_CREDENTIALS
from library.status.monitorstatus import CHECK_COUNT
import library.migrationlogger as migrationlogger

logger = migrationlogger.get_logger(os.path.basename(__file__))
SEC_CREDENTIALS_URL = 'https://synthetics.newrelic.com/synthetics/api/v1/secure-credentials'
query_secure_credentials_for = "FROM SyntheticCheck SELECT uniques(secureCredentials), count(monitorName) " \
                               "SINCE 7 days ago WHERE monitorName = "


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def from_script(script):
    secure_credentials = []
    decoded_script = base64.b64decode(script)
    for line in decoded_script.splitlines():
        words = line.decode().split(' ')  # this decode converts line to a str
        for word in words:
            if word.startswith("$secure."):
                print(word)
    return secure_credentials


# returns set of secureCredentials and number of checks run ,
# checkCount of 0 indicates monitor hasn't been run in the past week
def from_insights(insights_query_key, account_id, monitor_name):
    logger.info("Fetching secure credentials for " + monitor_name)
    escaped_monitor_name = escape(monitor_name)
    query = query_secure_credentials_for + "'" + escaped_monitor_name + "'"
    secure_credentials = []
    credentials_and_checks = {SEC_CREDENTIALS: secure_credentials, CHECK_COUNT: 0}
    result = insightsclient.execute(insights_query_key, account_id, query)
    if result['status'] == 200:
        results_json = result['json']
        secure_credentials = results_json['results'][0]['members']
        while '' in secure_credentials:  # remove empties
            secure_credentials.remove('')
        if len(secure_credentials) > 0 and ',' in secure_credentials[0]:
            secure_credentials = secure_credentials[0].split(',')
        credentials_and_checks[SEC_CREDENTIALS] = secure_credentials
        credentials_and_checks[CHECK_COUNT] = results_json['results'][1]['count']
    return credentials_and_checks


def escape(monitor_name):
    if '\\' in monitor_name:
        escaped_monitor_name = monitor_name.replace('\\', '\\\\')
        logger.info('escaped name : ' + escaped_monitor_name)
        return escaped_monitor_name
    return monitor_name


def create(api_key, scripted_monitors):
    sec_creds_set = get_unique_credentials(scripted_monitors)
    secure_credential_status = {}
    for secure_cred in sec_creds_set:
        sec_cred_data = {'key': secure_cred, 'value': 'dummy',
                         'description': 'PLEASE UPDATE. Created by migration script.'}
        sec_cred_json_str = json.dumps(sec_cred_data)
        response = requests.post(SEC_CREDENTIALS_URL, headers=setup_headers(api_key), data=sec_cred_json_str)
        status = {'sec_cred_status': response.status_code}
        if response.text:
            status['body'] = response.text
        secure_credential_status[secure_cred] = status
        logger.debug(secure_credential_status)
    return secure_credential_status


def get_unique_credentials(scripted_monitors):
    secure_credentials_set = set()
    for scripted_monitor in scripted_monitors:
        if CHECK_COUNT in scripted_monitor:
            if SEC_CREDENTIALS in scripted_monitor:
                if scripted_monitor[CHECK_COUNT] > 0 and len(scripted_monitor[SEC_CREDENTIALS]) > 0:
                    secure_credentials_set.update(set(scripted_monitor[SEC_CREDENTIALS]))
    return secure_credentials_set


def delete_all(api_key, account_id):
    logger.warn('Deleting all secure credentials for ' + account_id)
    result = requests.get(SEC_CREDENTIALS_URL, headers=setup_headers(api_key))
    if result.status_code == 200:
        response_json = result.json()
        sec_creds = response_json['secureCredentials']
        for sec_cred in sec_creds:
            logger.info('Deleting ' + sec_cred['key'])
            result = requests.delete(SEC_CREDENTIALS_URL + '/' + sec_cred['key'], headers=setup_headers(api_key))
            logger.info('Delete status ' + str(result.status_code))