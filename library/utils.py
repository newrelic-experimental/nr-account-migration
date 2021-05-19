import os
import sys
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.clients.entityclient as ec
import library.localstore as store
import logging
import json
import requests
import configparser
import argparse

DEFAULT_INDENT = 2

NORMAL_PAGINATION = 'normal'
INFRA_PAGINATION = 'infra'
logger = m_logger.get_logger(os.path.basename(__file__))

def configure_loglevel(args):
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
        
    m_logger.set_log_level(log_level)

def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'application/json'}


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
def get_paginated_entities(api_key, fetch_url, entity_key, params={}, pageType=NORMAL_PAGINATION):
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
            if pageType == INFRA_PAGINATION:
                # Infrastrucure alerts API handles pagination via offset and limit parameters
                next_url = ''
                if resp_json['meta']['total'] > (resp_json['meta']['limit'] + resp_json['meta']['offset']):
                    next_url = curr_fetch_url
                    params['offset'] = params['offset'] + params['limit']
            else:
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
    if 'targetApiKey' in args and args.targetApiKey:
        api_key = args.targetApiKey[0]
    elif 'target_api_key' in args and args.target_api_key:
        api_key = args.target_api_key[0]
    else:
        api_key = os.environ.get('ENV_TARGET_API_KEY')
    return api_key


def ensure_source_api_key(args):
    if 'sourceApiKey' in args and args.sourceApiKey:
        api_key = args.sourceApiKey[0]
    elif 'source_api_key' in args and args.source_api_key:
        api_key = args.source_api_key[0]
    else:
        api_key = os.environ.get('ENV_SOURCE_API_KEY')
    return api_key

def error_and_exit(param_name, env_name):
    error_message_and_exit('Error: Missing param ' + param_name + ' or env variable ' + env_name)

def error_message_and_exit(msg):
    logger.error(msg)
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


def load_alert_policy_names(policyNameFile, entityNameFile, account_id, api_key, use_local):
    names = set()
    if policyNameFile:
        policy_names = store.load_names(policyNameFile)
        names.update(set(policy_names))

    if entityNameFile:
        entity_names = store.load_names(entityNameFile)
        if entity_names:
            policy_names = ac.get_policy_names_by_entities(entity_names, account_id, api_key, use_local)
            if policy_names:
                names.update(set(policy_names))

    return list(names)

def config_get(
    config: configparser.ConfigParser, 
    section_name: str,
    key: str
) -> str:
    value = config.get(section_name, key)
    if value:
        return value

    return os.environ.get('ENV_%s' % key.upper())

def process_base_config(
    config: configparser.ConfigParser,
    section_name: str,
    args: argparse.Namespace
) -> dict:
    source_account_id = config_get(
        config,
        section_name,
        'source_account_id'
    )
    if not source_account_id:
        if not args.source_account_id:
            error_message_and_exit('A source account ID is required')
        source_account_id = args.source_account_id[0]

    target_account_id = config_get(
        config,
        section_name,
        'target_account_id'
    )
    if not target_account_id:
        if not args.target_account_id:
            error_message_and_exit('A target account ID is required')
        target_account_id = args.target_account_id[0]

    source_api_key = config_get(config, section_name, 'source_api_key')
    if not source_api_key:
        if not args.source_api_key:
            error_message_and_exit('A Source API key is required')
        source_api_key = args.source_api_key[0]

    target_api_key = config_get(config, section_name, 'target_api_key')
    if not target_api_key:
        if not args.target_api_key:
            error_message_and_exit('A Target API key is required')
        target_api_key = args.target_api_key[0]

    return {
        'source_account_id': source_account_id,
        'target_account_id': target_account_id,
        'source_api_key': source_api_key,
        'target_api_key': target_api_key,
    }