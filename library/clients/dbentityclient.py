import requests
import json
import os
import library.utils as utils
import library.nrpylogger as nrpy_logger
import library.clients.gql as nerdgraph

logger = nrpy_logger.get_logger(os.path.basename(__file__))


class DashboardEntity:

    def __init__(self):
        pass

    @staticmethod
    def get(user_api_key, guid):
        payload = DashboardEntity._get_dashboard_payload(guid)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload)

    @staticmethod
    def get_pages_widgets(user_api_key, guid):
        payload = DashboardEntity._get_pages_widgets_payload(guid)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload)

    @staticmethod
    def create(user_api_key, account_id, dashboard):
        payload = DashboardEntity._create_dashboard_payload(account_id, dashboard)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(user_api_key, payload)

    @staticmethod
    def update_page_widgets(user_api_key, page_guid, widgets):
        mutation_query = '''mutation($guid: EntityGuid!,$widgets: [DashboardUpdateWidgetInput!]!) {
                                dashboardUpdateWidgetsInPage(guid: $guid, widgets: $widgets) {
                                        errors { description type }
                                }
                            }'''
        payload = {'query': mutation_query, 'variables': {'guid': page_guid, 'widgets': widgets}}
        return nerdgraph.GraphQl.post(user_api_key, payload)

    @staticmethod
    def _create_dashboard_payload(account_id, dashboard):
        mutation_query = '''mutation($accountId: Int!, $dashboard: DashboardInput!) {                    
                    dashboardCreate(accountId: $accountId , dashboard: $dashboard) {
                        entityResult { guid name }
                        errors { description }
                    }
                }'''
        return {'query': mutation_query, 'variables': {'accountId': account_id, 'dashboard': dashboard}}


    @staticmethod
    def _get_dashboard_payload(guid):
        dashboard_query = '''query($guid: EntityGuid!) { 
                                actor {
                                    entity(guid: $guid) {
                                      ... on DashboardEntity {                                        
                                        name
                                        permissions
                                        pages {
                                          name
                                          widgets {
                                            visualization { id }
                                            title
                                            layout { row width height column }
                                            rawConfiguration
                                            linkedEntities {
                                              accountId
                                              entityType                                              
                                              name
                                              guid
                                            }
                                          }
                                        }
                                      }                               
                                    } 
                                } 
                            }'''
        variables = {'guid': guid}
        return {'query': dashboard_query, 'variables': variables}

    @staticmethod
    def _get_pages_widgets_payload(guid):
        dashboard_query = '''query($guid: EntityGuid!) { 
                                    actor {
                                        entity(guid: $guid) {
                                          ... on DashboardEntity {                                        
                                          name
                                            pages {
                                              name
                                              guid
                                              widgets {
                                                id
                                                title
                                                visualization { id }                                                
                                                layout { row width height column }
                                                rawConfiguration                                                
                                              }          
                                            }  
                                          }                               
                                        } 
                                    } 
                                }'''
        variables = {'guid': guid}
        return {'query': dashboard_query, 'variables': variables}
