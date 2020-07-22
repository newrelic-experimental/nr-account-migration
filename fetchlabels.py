import argparse
import os
import requests
import json
import time
import library.migrationlogger as migrationlogger
import library.localstore as store
from library.utils import get_next_url


logger = migrationlogger.get_logger(os.path.basename(__file__))
get_labels_url = 'https://api.newrelic.com/v2/labels.json'
get_monitors_for_label = 'https://synthetics.newrelic.com/synthetics/api/v4/monitors/labels/'

parser = argparse.ArgumentParser(description='Get all labels')


def setup_params():
    parser.add_argument('--sourceAccount', nargs=1, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, required=False, help='Source API Key or \
    set env var ENV_SOURCE_API_KEY')


def setup_headers(api_key):
    return {'X-Api-Key': api_key}


def print_params():
    logger.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    logger.info("Using sourceApiKey : " + len(source_api_key[:-4])*"*"+source_api_key[-4:])


def fetch_all_labels(api_key):
    labels_response = requests.get(get_labels_url, headers=setup_headers(api_key))
    if labels_response.status_code != 200:
        logger.fatal("Error getting labels " + labels_response.text)
    labels_json = json.loads(labels_response.text)
    logger.info("Fetched all labels : " + str(len(labels_json['labels'])))
    return labels_json


def fetch_monitors_for_label(api_key, monitor_labels,label):
    another_page = True
    error = False
    monitors_for_labels_url = get_monitors_for_label + label['key']
    logger.debug("Fetching monitors for : " + label['key'])
    while another_page and error is False:
        resp = requests.get(monitors_for_labels_url, headers=setup_headers(api_key))
        if resp.status_code == 200:
            resp_json = json.loads(resp.text)
            for monitor in resp_json['pagedData']['monitorRefs']:
                if monitor['id'] in monitor_labels:
                    monitor_labels[monitor['id']].append(label['key'])
                else:
                    monitor_labels[monitor['id']] = [label['key']]
            next_url = get_next_url(resp.headers)
            if next_url:
                monitors_for_labels_url = next_url
            else:
                another_page = False
        else:
            another_page = False
            error = True
            logger.error(
                'ERROR - Get API call to retrieve current label/monitor mapping failed!  Response code: ' + str(
                    resp.status_code))


def update_apm_labels(apm_labels, apm_apps, label):
    for app_id in apm_apps:
        apm_app = str(app_id)
        if apm_app in apm_labels:
            apm_labels[apm_app].append(label['key'])
        else:
            apm_labels[apm_app] = [label['key']]


def fetch_labels(api_key, account_id):
    labels_json = fetch_all_labels(api_key)
    monitor_labels = {}
    apm_labels = {}
    logger.debug("Now fetching synthetic monitors for each label")
    for label in labels_json['labels']:
        fetch_monitors_for_label(api_key, monitor_labels, label)
        update_apm_labels(apm_labels, label['origins']['apm'], label)
    labels_dir = store.create_labels_dir(account_id)
    store.save_monitor_labels(labels_dir, monitor_labels)
    store.save_monitor_labels_csv(labels_dir, monitor_labels)
    logger.info('Stored labels for ' + str(len(monitor_labels)) + ' monitors in ' + str(labels_dir))
    store.save_apm_labels(labels_dir, apm_labels)
    logger.info('Stored labels for ' + str(len(apm_labels)) + ' APM apps in ' + str(labels_dir))


if __name__ == '__main__':
    start_time = time.time()
    setup_params()
    args = parser.parse_args()
    source_api_key = ''
    if args.sourceApiKey:
        source_api_key = args.sourceApiKey[0]
    else:
        source_api_key = os.environ.get('ENV_SOURCE_API_KEY')
    if not source_api_key:
        logger.error('Error: Missing API Key. either pass as param ---sourceApiKey or \
                environment variable ENV_SOURCE_API_KEY.\n \
                e.g. export SOURCE_API_KEY="NRNA7893asdfhkh"')
    print_params()
    fetch_labels(source_api_key, str(args.sourceAccount[0]))
    logger.info("Time taken : " + str(time.time() - start_time) + "seconds")