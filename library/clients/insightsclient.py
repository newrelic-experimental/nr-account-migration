import os
import requests
import library.migrationlogger as m_logger
from library.clients.endpoints import Endpoints


PERF_STATS = 'performanceStats'
METADATA = 'metadata'

log = m_logger.get_logger(os.path.basename(__file__))


def setup_headers(api_key):
    return {'X-Query-Key': api_key, 'Content-Type': 'Application/JSON'}


def execute(insights_query_key, account_id, insights_query, region=Endpoints.REGION_US):
    log.debug(insights_query)
    query_params = {'nrql': insights_query}
    query_url = Endpoints.of(region).INSIGHTS_URL % account_id
    response = requests.get(query_url, headers=setup_headers(insights_query_key),
                            params=query_params)
    result = {'status': response.status_code}
    if response.status_code == 200:
        results_json = response.json()
        cleanup_results(results_json)
        result['json'] = results_json
    else:
        log.error(response.text)
        result['error'] = response.text
    return result


def cleanup_results(results_json):
    if PERF_STATS in results_json:
        results_json.pop(PERF_STATS)
    if METADATA in results_json:
        results_json.pop(METADATA)
