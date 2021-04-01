import requests
import os
import json
import library.migrationlogger as migrationlogger
import library.utils as utils

logger = migrationlogger.get_logger(os.path.basename(__file__))

ALERT_VIOLATIONS_URL = 'https://api.newrelic.com/v2/alerts_violations.json'
VIOLATIONS = 'violations'


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def get_all_alert_violations(api_key, start_date, end_date, only_open):
    params = {'start_date': start_date, 'end_date': end_date, 'only_open': only_open}
    return utils.get_paginated_entities(api_key, ALERT_VIOLATIONS_URL, VIOLATIONS, params)
