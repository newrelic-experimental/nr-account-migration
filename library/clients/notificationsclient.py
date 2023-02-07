import json
import os
import library.utils as utils
import library.migrationlogger as nrlogger
import library.clients.gql as nerdgraph

DESTINATION_TYPE_EMAIL = 'EMAIL'
DESTINATION_TYPE_EVENT_BRIDGE = 'EVENT_BRIDGE'
DESTINATION_TYPE_JIRA = 'JIRA'
DESTINATION_TYPE_MOBILE_PUSH = 'MOBILE_PUSH'
DESTINATION_TYPE_PAGERDUTY_ACCOUNT_INTEGRATION = 'PAGERDUTY_ACCOUNT_INTEGRATION'
DESTINATION_TYPE_PAGERDUTY_SERVICE_INTEGRATION = 'PAGERDUTY_SERVICE_INTEGRATION'
DESTINATION_TYPE_SERVICE_NOW = 'SERVICE_NOW'
DESTINATION_TYPE_SLACK = 'SLACK'
DESTINATION_TYPE_SLACK_COLLABORATION = 'SLACK_COLLABORATION'
DESTINATION_TYPE_SLACK_LEGACY = 'SLACK_LEGACY'
DESTINATION_TYPE_WEBHOOK = 'WEBHOOK'

SUPPORTED_DESTINATIONS = [
    DESTINATION_TYPE_EMAIL, 
    DESTINATION_TYPE_MOBILE_PUSH, 
    DESTINATION_TYPE_SLACK_LEGACY, 
    DESTINATION_TYPE_WEBHOOK
]

CHANNEL_PRODUCT_ALERTS = 'ALERTS'
CHANNEL_PRODUCT_DISCUSSIONS = 'DISCUSSIONS'
CHANNEL_PRODUCT_ERROR_TRACKING = 'ERROR_TRACKING'
CHANNEL_PRODUCT_IINT = 'IINT'
CHANNEL_PRODUCT_NTFC = 'NTFC'
CHANNEL_PRODUCT_PD = 'PD'
CHANNEL_PRODUCT_SHARING = 'SHARING'

CHANNEL_TYPE_EMAIL = 'EMAIL'
CHANNEL_TYPE_EVENT_BRIDGE = 'EVENT_BRIDGE'
CHANNEL_TYPE_JIRA_CLASSIC = 'JIRA_CLASSIC'
CHANNEL_TYPE_JIRA_NEXTGEN = 'JIRA_NEXTGEN'
CHANNEL_TYPE_MOBILE_PUSH = 'MOBILE_PUSH'
CHANNEL_TYPE_PAGERDUTY_ACCOUNT_INTEGRATION = 'PAGERDUTY_ACCOUNT_INTEGRATION'
CHANNEL_TYPE_PAGERDUTY_SERVICE_INTEGRATION = 'PAGERDUTY_SERVICE_INTEGRATION'
CHANNEL_TYPE_SERVICENOW_EVENTS = 'SERVICENOW_EVENTS'
CHANNEL_TYPE_SERVICENOW_INCIDENTS = 'SERVICENOW_INCIDENTS'
CHANNEL_TYPE_SLACK = 'SLACK'
CHANNEL_TYPE_SLACK_COLLABORATION = 'SLACK_COLLABORATION'
CHANNEL_TYPE_SLACK_LEGACY = 'SLACK_LEGACY'
CHANNEL_TYPE_WEBHOOK = 'WEBHOOK'

logger = nrlogger.get_logger(os.path.basename(__file__))


class NotificationsClient:

    def __init__(self):
        pass


    @staticmethod
    def query(func, user_api_key, account_id, region, cursor):
        payload = func(account_id, cursor)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload, region)


    @staticmethod
    def create_email_destination(destination, user_api_key, account_id, region):
        logger.info(f"Destination {destination['name']} creation started.")
        payload = NotificationsClient.email_destination_payload(account_id, destination)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateDestination']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateDestination']['error']}")
            else:
                destination_id =  result['response']['data']['aiNotificationsCreateDestination']['destination']['id']
                destination.setdefault('targetDestinationId', destination_id)
                logger.info(f"Destination {destination['name']} with id {destination['targetDestinationId']} creation complete.")
        return result


    @staticmethod
    def create_webhook_destination(destination, user_api_key, account_id, region):
        logger.info(f"Destination {destination['name']} creation started.")
        payload = NotificationsClient.webhook_destination_payload(account_id, destination)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateDestination']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateDestination']['error']}")
            else:
                destination_id =  result['response']['data']['aiNotificationsCreateDestination']['destination']['id']
                destination.setdefault('targetDestinationId', destination_id)
                logger.info(f"Destination {destination['name']} with id {destination['targetDestinationId']} creation complete.")
        return result


    @staticmethod
    def create_mobile_push_destination(destination, user_api_key, account_id, region):
        logger.info(f"Destination {destination['name']} creation started.")
        payload = NotificationsClient.mobile_push_destination_payload(account_id, destination)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateDestination']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateDestination']['error']}")
            else:
                destination_id =  result['response']['data']['aiNotificationsCreateDestination']['destination']['id']
                destination.setdefault('targetDestinationId', destination_id)
                logger.info(f"Destination {destination['name']} with id {destination['targetDestinationId']} creation complete.")
        return result


    @staticmethod
    def create_slack_legacy_destination(destination, user_api_key, account_id, region):
        logger.info(f"Destination {destination['name']} creation started.")
        payload = NotificationsClient.slack_legacy_destination_payload(account_id, destination)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateDestination']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateDestination']['error']}")
            else:
                destination_id =  result['response']['data']['aiNotificationsCreateDestination']['destination']['id']
                destination.setdefault('targetDestinationId', destination_id)
                logger.info(f"Destination {destination['name']} with id {destination['targetDestinationId']} creation complete.")
        return result


    @staticmethod
    def delete_all_destinations(destinations_by_id, user_api_key, account_id, region):
        logger.info(f"Destination deletion for account {account_id} started.")
        for destination in destinations_by_id.values():
            NotificationsClient.delete_destination(destination, user_api_key, account_id, region)
        logger.info(f"Destination deletion for account {account_id} complete.")


    @staticmethod
    def delete_destination(destination, user_api_key, account_id, region):
        logger.info(f"Destination {destination['name']} with id {destination['id']} deletion started.")
        payload = NotificationsClient.delete_destination_payload(account_id, destination['id'])
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsDeleteDestination']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsDeleteDestination']['error']}")
            else:
                logger.info(f"Destination {destination['name']} with id {destination['id']} deletion complete.")
        return result


    @staticmethod
    def create_email_channel(channel, user_api_key, account_id, region):
        logger.info(f"Channel {channel['name']} creation started.")
        payload = NotificationsClient.email_channel_payload(account_id, channel)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateChannel']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateChannel']['error']}")
            else:
                channel_id = result['response']['data']['aiNotificationsCreateChannel']['channel']['id']
                channel.setdefault('targetChannelId', channel_id)
                logger.info(f"Channel {channel['name']} with id {channel['targetChannelId']} creation complete.")
        return result


    @staticmethod
    def create_webhook_channel(channel, user_api_key, account_id, region):
        logger.info(f"Channel {channel['name']} creation started.")
        payload = NotificationsClient.webhook_channel_payload(account_id, channel)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateChannel']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateChannel']['error']}")
            else:
                channel_id = result['response']['data']['aiNotificationsCreateChannel']['channel']['id']
                channel.setdefault('targetChannelId', channel_id)
                logger.info(f"Channel {channel['name']} with id {channel['targetChannelId']} creation complete.")
        return result


    @staticmethod
    def create_mobile_push_channel(channel, user_api_key, account_id, region):
        logger.info(f"Channel {channel['name']} creation started.")
        payload = NotificationsClient.mobile_push_channel_payload(account_id, channel)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateChannel']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateChannel']['error']}")
            else:
                channel_id = result['response']['data']['aiNotificationsCreateChannel']['channel']['id']
                channel.setdefault('targetChannelId', channel_id)
                logger.info(f"Channel {channel['name']} with id {channel['targetChannelId']} creation complete.")
        return result


    @staticmethod
    def create_slack_legacy_channel(channel, user_api_key, account_id, region):
        logger.info(f"Channel {channel['name']} creation started.")
        payload = NotificationsClient.slack_legacy_channel_payload(account_id, channel)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsCreateChannel']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsCreateChannel']['error']}")
            else:
                channel_id = result['response']['data']['aiNotificationsCreateChannel']['channel']['id']
                channel.setdefault('targetChannelId', channel_id)
                logger.info(f"Channel {channel['name']} with id {channel['targetChannelId']} creation complete.")
        return result


    @staticmethod
    def delete_all_channels(channels_by_id, user_api_key, account_id, region):
        logger.info(f"Channel deletion for account {account_id} started.")
        for channel in channels_by_id.values():
            NotificationsClient.delete_channel(channel, user_api_key, account_id, region)
        logger.info(f"Channel deletion for account {account_id} complete.")


    @staticmethod
    def delete_channel(channel, user_api_key, account_id, region):
        logger.info(f"Channel {channel['name']} with id {channel['id']} deletion started.")
        payload = NotificationsClient.delete_channel_payload(account_id, channel['id'])
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiNotificationsDeleteChannel']['error'] is not None:
                logger.error(f"Error : {result['response']['data']['aiNotificationsDeleteChannel']['error']}")
            else:
                logger.info(f"Channel {channel['name']} with id {channel['id']} deletion complete.")
        return result


    @staticmethod
    def destinations(account_id, cursor):
        query = '''query($accountId: Int!, $cursor: String) {
                    actor {
                        account(id: $accountId) {
                            aiNotifications {
                                destinations (cursor: $cursor) {
                                    entities {
                                        id
                                        name
                                        active
                                        createdAt
                                        properties {
                                        displayValue
                                        key
                                        label
                                        value
                                        }
                                        status
                                        type
                                        updatedAt
                                        updatedBy
                                        accountId
                                        isUserAuthenticated
                                        lastSent
                                    }
                                    error {
                                        details
                                        description
                                        type
                                    }
                                    nextCursor
                                    totalCount
                                }
                            }
                        }
                    }
                }'''
        variables = {'accountId': account_id, 'cursor': cursor}
        return {'query': query, 'variables': variables}


    @staticmethod
    def channels(account_id, cursor):
        query = '''query($accountId: Int!, $cursor: String) {
                    actor {
                        account(id: $accountId) {
                            aiNotifications {
                                channels (cursor: $cursor) {
                                    entities {
                                        accountId
                                        active
                                        createdAt
                                        destinationId
                                        id
                                        name
                                        product
                                        properties {
                                            displayValue
                                            key
                                            label
                                            value
                                        }
                                        status
                                        type
                                        updatedBy
                                        updatedAt
                                    }
                                    error {
                                        description
                                        details
                                        type
                                    }
                                    nextCursor
                                    totalCount
                                }
                            }
                        }
                    }
                }'''
        variables = {'accountId': account_id, 'cursor': cursor}
        return {'query': query, 'variables': variables}


    @staticmethod
    def email_destination_payload(account_id, destination):
        mutation = '''mutation ($accountId: Int!, $destinationName: String!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateDestination(accountId: $accountId, destination: {
                name: $destinationName,
                properties: $properties,
                type: EMAIL
            }) {
                destination {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'destinationName': destination['name'],
                'properties': destination['properties']
            }
        }


    @staticmethod
    def webhook_destination_payload(account_id, destination):
        mutation = '''mutation ($accountId: Int!, $destinationName: String!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateDestination(accountId: $accountId, destination: {
                name: $destinationName,
                properties: $properties,
                type: WEBHOOK
            }) {
                destination {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'destinationName': destination['name'],
                'properties': destination['properties']
            }
        }


    @staticmethod
    def mobile_push_destination_payload(account_id, destination):
        mutation = '''mutation ($accountId: Int!, $destinationName: String!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateDestination(accountId: $accountId, destination: {
                name: $destinationName,
                properties: $properties,
                type: MOBILE_PUSH
            }) {
                destination {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'destinationName': destination['name'],
                'properties': destination['properties']
            }
        }


    @staticmethod
    def slack_legacy_destination_payload(account_id, destination):
        mutation = '''mutation ($accountId: Int!, $destinationName: String!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateDestination(accountId: $accountId, destination: {
                name: $destinationName,
                properties: $properties,
                type: SLACK_LEGACY
            }) {
                destination {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'destinationName': destination['name'],
                'properties': destination['properties']
            }
        }


    @staticmethod
    def delete_destination_payload(account_id, destination_id):
        mutation = '''mutation ($accountId: Int!, $destinationId: ID!) {
            aiNotificationsDeleteDestination(accountId: $accountId, destinationId: $destinationId) {
                ids
                error {
                    details
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'destinationId': destination_id
            }
        }


    @staticmethod
    def email_channel_payload(account_id, channel):
        mutation = '''mutation ($accountId: Int!, $channelName: String!, $destinationId: ID!, $product: AiNotificationsProduct!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateChannel(accountId: $accountId, channel: {
                destinationId: $destinationId,
                name: $channelName,
                product: $product,
                properties: $properties,
                type: EMAIL
            }) {
                channel {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'channelName': channel['name'],
                'destinationId': channel['destinationId'],
                'product': channel['product'],
                'properties': channel['properties']
            }
        }


    @staticmethod
    def webhook_channel_payload(account_id, channel):
        mutation = '''mutation ($accountId: Int!, $channelName: String!, $destinationId: ID!, $product: AiNotificationsProduct!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateChannel(accountId: $accountId, channel: {
                destinationId: $destinationId,
                name: $channelName,
                product: $product,
                properties: $properties,
                type: WEBHOOK
            }) {
                channel {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'channelName': channel['name'],
                'destinationId': channel['destinationId'],
                'product': channel['product'],
                'properties': channel['properties']
            }
        }


    @staticmethod
    def mobile_push_channel_payload(account_id, channel):
        mutation = '''mutation ($accountId: Int!, $channelName: String!, $destinationId: ID!, $product: AiNotificationsProduct!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateChannel(accountId: $accountId, channel: {
                destinationId: $destinationId,
                name: $channelName,
                product: $product,
                properties: $properties,
                type: MOBILE_PUSH
            }) {
                channel {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'channelName': channel['name'],
                'destinationId': channel['destinationId'],
                'product': channel['product'],
                'properties': channel['properties']
            }
        }


    @staticmethod
    def slack_legacy_channel_payload(account_id, channel):
        mutation = '''mutation ($accountId: Int!, $channelName: String!, $destinationId: ID!, $product: AiNotificationsProduct!, $properties: [AiNotificationsPropertyInput!]!) {
            aiNotificationsCreateChannel(accountId: $accountId, channel: {
                destinationId: $destinationId,
                name: $channelName,
                product: $product,
                properties: $properties,
                type: SLACK_LEGACY
            }) {
                channel {
                    id
                    name
                }
                error {
                    ... on AiNotificationsResponseError {
                        description
                        details
                        type
                    }
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'channelName': channel['name'],
                'destinationId': channel['destinationId'],
                'product': channel['product'],
                'properties': channel['properties']
            }
        }


    @staticmethod
    def delete_channel_payload(account_id, channel_id):
        mutation = '''mutation ($accountId: Int!, $channelId: ID!) {
            aiNotificationsDeleteChannel(accountId: $accountId, channelId: $channelId) {
                ids
                error {
                    details
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'channelId': channel_id
            }
        }
