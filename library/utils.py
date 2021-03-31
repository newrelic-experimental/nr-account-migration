import os
import sys
import library.migrationlogger as m_logger
import library.clients.entityclient as ec
import json
import requests


DEFAULT_INDENT = 2
logger = m_logger.get_logger(os.path.basename(__file__))


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def get_next_url(rsp_headers):
    next_url = ''
    try:
        link = rsp_headers['link']
        if len(link) > 0:
            all_links = link.split(',')
            for jj in range(0, len(all_links)):
                curr_link = all_links[jj].split(';')
                if 'next' in curr_link[1]:
                    next_url = curr_link[0].strip()
                    next_url = next_url[1:-1]
    except KeyError:
        pass
    return next_url


# Logic borrowed from Brian Peck
# returns all_entities { response_count : COUNT, entity_key : [] }
def get_paginated_entities(api_key, fetch_url, entity_key, params={}):
    another_page = True
    error = False
    curr_fetch_url = fetch_url
    all_entities = {'response_count': 0, entity_key: []}
    while another_page and error is False:
        resp = requests.get(curr_fetch_url, headers=setup_headers(api_key), params=params)
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)
            all_entities[entity_key].extend(resp_json[entity_key])
            all_entities['response_count'] = all_entities['response_count'] + len(resp_json[entity_key])
            next_url = get_next_url(resp.headers)
            if next_url:
                curr_fetch_url = next_url
            else:
                another_page = False
        else:
            another_page = False
            error = True
            logger.error(
                'ERROR - Get API call to retrieve ' + entity_key + ' failed!  Response code: ' + str(
                    resp.status_code))
            continue
    return all_entities


# add an array to the dictionary if it does not exist else append the array to the existing dictionary value
def append_or_insert(input_dict, input_id, key, value):
    if input_id in input_dict:
        input_dict[input_id][key].append(value)
    else:
        input_dict[input_id] = {key: [value]}


def file_name_from(path):
    path_elements = path.split('/')
    file_element = path_elements[len(path_elements) - 1]
    file_name = file_element.split('.')[0]
    return file_name


def ensure_target_api_key(args):
    if args.targetApiKey:
        api_key = args.targetApiKey[0]
    else:
        api_key = os.environ.get('ENV_TARGET_API_KEY')
    return api_key


def ensure_source_api_key(args):
    if args.sourceApiKey:
        api_key = args.sourceApiKey[0]
    else:
        api_key = os.environ.get('ENV_SOURCE_API_KEY')
    return api_key


def ensure_personal_api_key(args):
    if args.personalApiKey:
        api_key = args.personalApiKey[0]
    else:
        api_key = os.environ.get('ENV_PERSONAL_API_KEY')
    return api_key


def error_and_exit(param_name, env_name):
    logger.error('Error: Missing param ' + param_name + ' or env variable ' + env_name)
    sys.exit()


def get_entity_type(app_condition):
    if app_condition['type'] in ['apm_app_metric', 'apm_jvm_metric']:
        return ec.APM_APP
    if app_condition['type'] == 'browser_metric':
        return ec.BROWSER_APP
    if app_condition['type'] == 'apm_kt_metric':
        return ec.APM_KT
    if app_condition['type'] == 'mobile_metric':
        return ec.MOBILE_APP
    logger.error('entity type not supported for ' + app_condition['type'])
    return 'UNSUPPORTED'


def get_condition_prefix(entity_type):
    if ec.APM_APP == entity_type:
        return '-acon'
    if ec.BROWSER_APP == entity_type:
        return '-bcon'
    if ec.MOBILE_APP == entity_type:
        return '-mcon'
    if ec.APM_KT == entity_type:
        return '-ktcon'
