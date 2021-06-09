import argparse
import os
import sys
import library.localstore as store
import library.migrationlogger as m_logger
import library.utils as utils
import library.clients.insightsclient as insightsclient


"""Get Data being reported from  a host
Query Metrics being reported
Query Events being reported
"""
logger = m_logger.get_logger(os.path.basename(__file__))


def configure_parser(is_standalone: bool = True):
    parser = argparse.ArgumentParser(
        description='Get Metrics and Events reported from a host'
    )
    parser.add_argument(
        '--hostsFile',
        '--hosts_file',
        nargs=1,
        type=str,
        required=False,
        help='Path to file with host names',
        dest='hosts_file'
    )
    parser.add_argument(
        '--sourceAccount',
        '--source_account_id',
        nargs=1,
        type=int,
        required=is_standalone,
        help='Source accountId',
        dest='source_account_id'
    )
    parser.add_argument(
        '--sourceApiKey',
        '--source_api_key',
        nargs=1,
        type=str,
        required=False,
        help='Source account API Key or set environment variable ENV_SOURCE_API_KEY',
        dest='source_api_key'
    )
    parser.add_argument(
        '--insightsQueryKey',
        '--insights_query_key',
        nargs=1,
        type=str,
        required=False,
        help='Insights Query Key or set environment variable ENV_INSIGHTS_QUERY_KEY',
        dest='insights_query_key'
    )
    parser.add_argument(
        '--region',
        '--nr_region',
        nargs=1,
        type=str,
        required=False,
        default='us',
        help='NR Region us | eu (default : us)',
        dest='nr_region'
    )
    return parser


def fetch_all_event_types(query_key: str,acct_id : int, region: str):
    show_events_query = "SHOW EVENT TYPES"
    response = insightsclient.execute(query_key, acct_id, show_events_query, region)
    if 'error' in response:
        logger.error('Could not fetch event types')
        logger.error(response['error'])
        return []
    else:
        logger.info(response)
        return response['json']['results'][0]['eventTypes']


def fetch_event_type_count(host_name: str, event_type: str, query_key: str, acct_id: int, region: str):
    event_count_query_template = "FROM %(eventType)s SELECT COUNT(*) WHERE entityName = '%(host)s' SINCE 1 WEEK AGO"
    event_count_query = event_count_query_template % {'eventType': event_type, 'host': host_name}
    response = insightsclient.execute(query_key, acct_id, event_count_query, region)
    if 'error' in response:
        logger.error('Error executing query ' + event_count_query)
        logger.error('Error fetching event count ' + response)
        return 0
    else:
        return response['json']['results'][0]['count']


def fetch_metrics(host_name: str, query_key: str, acct_id: int, region: str):
    logger.info("fetching metrics for " + host_name)
    fetch_metrics_query = "FROM Metric SELECT uniques(metricName) " \
                          "WHERE entityName = '%s' " \
                          "SINCE 1 week ago LIMIT MAX" % host_name
    response = insightsclient.execute(query_key, acct_id, fetch_metrics_query, region)
    if 'error' in response:
        logger.error('Could not fetch metrics for %s', host_name)
        logger.error(response['error'])
        return []
    else:
        return response['json']['results'][0]['members']


def fetch_data_types(host_file_path: str, acct_id: int, api_key: str, query_key: str, region='us'):
    host_names = store.load_names(host_file_path)
    all_event_types = fetch_all_event_types(query_key, acct_id, region)
    for host_name in host_names:
        host_data = [['entityName', 'dataType', 'metricOrEventName']]
        logger.info('fetching data types for ' + host_name)
        dim_metrics = fetch_metrics(host_name, query_key, acct_id,  region)
        logger.info("Fetched metrics %d", len(dim_metrics))
        for dim_metric in dim_metrics:
            host_data.append([host_name, 'Metric', dim_metric])
        for event_type in all_event_types:
            if event_type != 'Metric':
                event_count = fetch_event_type_count(host_name, event_type, query_key, acct_id, region)
                if event_count > 0:
                    host_data.append([host_name, 'Event', event_type])
        logger.info("Total event and metrics found %d", len(host_data) - 1)
        if len(host_data) > 1:
            store.save_host_data_csv(host_name, host_data)
        else:
            logger.info('No metrics or events found for ' + host_name)


def main():
    parser = configure_parser()
    args = parser.parse_args()
    api_key = utils.ensure_source_api_key(args)
    if not api_key:
        utils.error_and_exit('api_key', 'ENV_SOURCE_API_KEY')
    insights_query_key = utils.ensure_insights_query_key(args)
    if not insights_query_key:
        utils.error_and_exit('query_api_key', 'ENV_QUERY_API_KEY')
    region = utils.ensure_region(args)
    hosts_file = args.hosts_file[0] if args.hosts_file else None
    if not hosts_file:
        logger.error('host file must be specified.')
        sys.exit()
    fetch_data_types(hosts_file, args.source_account_id[0], api_key, insights_query_key, region)


if __name__ == '__main__':
    main()
