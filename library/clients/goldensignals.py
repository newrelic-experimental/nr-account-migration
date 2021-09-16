import os
import json
import library.migrationlogger as logger
import library.clients.gql as nerdgraph
from library.clients.endpoints import Endpoints

logger = logger.get_logger(os.path.basename(__file__))


class GoldenSignals:

    def __init__(self, region=Endpoints.REGION_US):
        self.region = region
        pass

    def reset(self, user_api_key, workload_guid, domain, type):
        payload = GoldenSignals._reset_golden_signals_payload(workload_guid, domain, type)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload, self.region)


    def override(self, user_api_key, workload_guid, domain, type, metrics):
        payload = GoldenSignals._override_golden_signals_payload(workload_guid, domain, type, metrics)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload, self.region)

    @staticmethod
    def _reset_golden_signals_payload(workload_guid, domain, type):
        mutation_query = '''mutation($context: EntityGoldenContextInput!, $domainType: DomainTypeInput!) { 
                                entityGoldenMetricsReset(context: $context, domainType: $domainType) { 
                                    errors {message type} 
                                }                                     
                            }'''
        return {'query': mutation_query, 'variables': {'context': {'guid':  workload_guid},
                                                       'domainType': {'domain': domain, 'type': type}
                                                       }
                }

    @staticmethod
    def _override_golden_signals_payload(workload_guid, domain, type, metrics):

        mutation_query = '''mutation($context: EntityGoldenContextInput!, $domainType: DomainTypeInput!,
        $metrics: [EntityGoldenMetricInput!]!) {
            entityGoldenMetricsOverride(context: $context, domainType: $domainType, metrics: $metrics) {
                errors { message type }
                metrics { metrics { name query title } }
            }
        }
        '''
        return {'query': mutation_query, 'variables': {'context': {'guid': workload_guid},
                                                       'domainType': {'domain': domain, 'type': type},
                                                       'metrics': metrics
                                                       }
                }
