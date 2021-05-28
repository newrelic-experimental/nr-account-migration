import os
import library.migrationlogger as migrationlogger
import library.utils as utils
from library.clients.endpoints import Endpoints

logger = migrationlogger.get_logger(os.path.basename(__file__))

VIOLATIONS = 'violations'


def setup_headers(api_key):
    return {'Api-Key': api_key, 'Content-Type': 'Application/JSON'}


def get_all_alert_violations(api_key, start_date, end_date, only_open=False, region=Endpoints.REGION_US):
    params = {'start_date': start_date, 'end_date': end_date, 'only_open': only_open}
    return utils.get_paginated_entities(api_key, Endpoints.of(region).ALERT_VIOLATIONS_URL, VIOLATIONS, params)
