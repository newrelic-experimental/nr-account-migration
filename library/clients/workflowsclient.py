import json
import os
import library.utils as utils
import library.migrationlogger as nrlogger
import library.clients.gql as nerdgraph

logger = nrlogger.get_logger(os.path.basename(__file__))


class WorkflowsClient:

    def __init__(self):
        pass


    @staticmethod
    def query(func, user_api_key, account_id, region, cursor):
        payload = func(account_id, cursor)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload, region)


    @staticmethod
    def workflows(account_id, cursor):
        query = '''query($accountId: Int!, $cursor: String) {
                    actor {
                        account(id: $accountId) {
                            aiWorkflows {
                                workflows (cursor: $cursor) {
                                    entities {
                                        accountId
                                        createdAt
                                        destinationConfigurations {
                                            channelId
                                            name
                                            notificationTriggers
                                            type
                                        }
                                        destinationsEnabled
                                        enrichments {
                                            accountId
                                            configurations {
                                                ... on AiWorkflowsNrqlConfiguration {
                                                query
                                                }
                                            }
                                            createdAt
                                            id
                                            name
                                            type
                                            updatedAt
                                        }
                                        enrichmentsEnabled
                                        id
                                        issuesFilter {
                                            accountId
                                            id
                                            name
                                            predicates {
                                                attribute
                                                operator
                                                values
                                            }
                                            type
                                        }
                                        lastRun
                                        mutingRulesHandling
                                        name
                                        updatedAt
                                        workflowEnabled
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
    def create_workflow(workflow, user_api_key, account_id, region):
        logger.info(f"Workflow {workflow['name']} creation started.")
        workflowData = {}
        workflowKeysToCopy = set([
            'destinationsEnabled',
            'enrichmentsEnabled',
            'mutingRulesHandling',
            'name',
            'workflowEnabled'
        ])
        # creating a shallow copy using for loop
        for key, value in workflow.items():
            if key in workflowKeysToCopy:
                workflowData[key] = value
        if len(workflow['enrichments']) < 1:
            workflowData['enrichments'] = None
        # Update channel id values in destinationConfigurations
        logger.info(f"Update channel id values in destinationConfigurations")
        if 'destinationConfigurations' in workflow:
            workflowData['destinationConfigurations'] = {
                'channelId':  workflow['destinationConfigurations'][0]['targetChannelId'],  # It's unclear why destination configurations is of type list, when there is only one channel permitted per workflow. From the docs[https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-api-workflows/#create-workflow]: Callout note: A channel ID is unique and so can't be used in multiple workflows or used multiple times in the same workflow.
                'notificationTriggers': workflow['destinationConfigurations'][0]['notificationTriggers']
            }
        # Update policy id values in issuesFilter
        logger.info(f"Update policy id values in issuesFilter")
        predicates = []
        for predicate in workflow['issuesFilter']['predicates']:
            if predicate['attribute'] == 'labels.policyIds':
                target_predicate = {
                    'attribute': predicate['attribute'],  # String!
                    'operator': predicate['operator'],  # iWorkflowsOperator!
                    'values': predicate['targetValues']  # [String!]!
                }
                predicates.append(target_predicate)
            else:
                logger.debug(f"Ignoring predicate {predicate}")
        if 'issuesFilter' in workflow:
            workflowData['issuesFilter'] = {
                'name': workflow['issuesFilter']['name'],  # String: this is a guid, which is unexpected
                'predicates': predicates,  # [AiWorkflowsPredicateInput!]!:
                'type': workflow['issuesFilter']['type']  # AiWorkflowsFilterType!:
            }
        payload = WorkflowsClient.workflow_payload(account_id, workflowData)
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if len(result['response']['data']['aiWorkflowsCreateWorkflow']['errors']) > 0:
                logger.error(f"Error : {result['response']['data']['aiWorkflowsCreateWorkflow']['errors']}")
            else:
                workflow_id =  result['response']['data']['aiWorkflowsCreateWorkflow']['workflow']['id']
                workflow.setdefault('targetWorkflowId', workflow_id)
                logger.info(f"Workflow {workflow['name']} with id {workflow['targetWorkflowId']} creation complete.")
        return result


    @staticmethod
    def workflow_payload(account_id, workflowData):
        mutation = '''mutation ($accountId: Int!, $workflowData: AiWorkflowsCreateWorkflowInput!) {
        aiWorkflowsCreateWorkflow(
            accountId: $accountId
            createWorkflowData: $workflowData) {
                workflow {
                    id
                    name
                    destinationConfigurations {
                        channelId
                        name
                        type
                        notificationTriggers
                    }
                    enrichmentsEnabled
                    destinationsEnabled
                    issuesFilter {
                        accountId
                        id
                        name
                        predicates {
                            attribute
                            operator
                            values
                        }
                        type
                    }
                    lastRun
                    workflowEnabled
                    mutingRulesHandling
                }
                errors {
                    description
                    type
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'workflowData': workflowData
            }
        }

    @staticmethod
    def delete_all_workflows(workflows_by_id, user_api_key, account_id, region, delete_channels=True):
        logger.info(f"Workflow deletion for account {account_id} started.")
        for workflow in workflows_by_id.values():
            WorkflowsClient.delete_workflow(workflow, user_api_key, account_id, region, delete_channels)
        logger.info(f"Workflow deletion for account {account_id} complete.")


    @staticmethod
    def delete_workflow(workflow, user_api_key, account_id, region, delete_channels=True):
        logger.info(f"Workflow {workflow['name']} with id {workflow['id']} deletion started.")
        payload = WorkflowsClient.delete_workflow_payload(account_id, delete_channels, workflow['id'])
        logger.debug(json.dumps(payload))
        result = nerdgraph.GraphQl.post(user_api_key, payload, region)
        if 'response' in result:
            if result['response']['data']['aiWorkflowsDeleteWorkflow']['errors'] is not None:
                logger.error(f"Error : {result['response']['data']['aiWorkflowsDeleteWorkflow']['errors']}")
            else:
                logger.info(f"Workflow {workflow['name']} with id {workflow['id']} deletion complete.")
        return result


    @staticmethod
    def delete_workflow_payload(account_id, delete_channels, id):
        mutation = '''mutation ($accountId: Int!, $deleteChannels: Boolean!, $id: ID!) {
            aiWorkflowsDeleteWorkflow(accountId: $accountId, deleteChannels: $deleteChannels, id: $id) {
                id
                errors {
                    description
                    type
                }
            }
        }'''
        return {
            'query': mutation,
            'variables': {
                'accountId': int(account_id),
                'deleteChannels': delete_channels,
                'id': id
            }
        }
