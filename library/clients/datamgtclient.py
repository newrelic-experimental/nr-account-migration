import json
import os
import library.utils as utils
import library.migrationlogger as nrlogger
import library.clients.gql as nerdgraph

logger = nrlogger.get_logger(os.path.basename(__file__))


class DataManagementClient:

    def __init__(self):
        pass

    @staticmethod
    def get_feature_settings(user_api_key, account_id, region):
        payload = DataManagementClient._query_feature_settings_payload(account_id)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload, region)

    @staticmethod
    def _query_feature_settings_payload(account_id):
        query = '''query($accountId: Int!) { 
                        actor {
                            account(id: $accountId) { dataManagement {
                                featureSettings {
                                    enabled
                                    key
                                    name
                                }
                            }}
                        }
                    }'''
        variables = {'accountId': account_id}
        return {'query': query, 'variables': variables}