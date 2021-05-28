import os
import library.migrationlogger as m_logger


class Endpoints:
    logger = m_logger.get_logger(os.path.basename(__file__))
    REGION_US = "us"
    REGION_EU = "eu"

    @classmethod
    def of(cls, region=REGION_US):
        if region == cls.REGION_US:
            return USEndpoints()
        elif region == cls.REGION_EU:
            return EUEndpoints()
        else:
            cls.logger.error("Incorrect region specified. Region can be either us or eu")


class USEndpoints:

    GRAPHQL_URL = 'https://api.newrelic.com/graphql'
    SHOW_APM_APP_URL = 'https://api.newrelic.com/v2/applications/'
    GET_APM_APP_URL = 'https://api.newrelic.com/v2/applications.json'
    GET_BROWSER_APP_URL = 'https://api.newrelic.com/v2/browser_applications.json'
    SHOW_MOBILE_APP_URL = 'https://api.newrelic.com/v2/mobile_applications/'
    SHOW_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions/'
    GET_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions.json'
    PUT_LABEL_URL = 'https://api.newrelic.com/v2/labels.json'
    GET_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards.json'
    SHOW_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards/'
    DEL_DASHBOARDS_URL = 'https://api.newrelic.com/v2/dashboards/'
    MONITORS_URL = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/'
    MONITORS_LABEL_URL = 'https://synthetics.newrelic.com/synthetics/api/v4/monitors/'
    INSIGHTS_URL = 'https://insights-api.newrelic.com/v1/accounts/%s/query'
    SEC_CREDENTIALS_URL = 'https://synthetics.newrelic.com/synthetics/api/v1/secure-credentials'
    ALERTS_CHANNEL_URL = 'https://api.newrelic.com/v2/alerts_channels.json'
    ALERT_POLICIES_URL = 'https://api.newrelic.com/v2/alerts_policies.json'
    ALERT_POLICY_CHANNELS_URL = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
    DEL_ALERTS_URL = 'https://api.newrelic.com/v2/alerts_policies/'
    DEL_CHANNELS_URL = 'https://api.newrelic.com/v2/alerts_channels/'
    GET_APP_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_conditions.json'
    APP_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_conditions/'
    CREATE_APP_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_conditions/policies/'
    GET_SYNTH_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_synthetics_conditions.json'
    CREATE_SYNTHETICS_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_synthetics_conditions/policies/'
    LOC_FAILURE_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_location_failure_conditions/policies/'
    NRQL_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_nrql_conditions.json'
    CREATE_NRQL_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_nrql_conditions/policies/'
    EXTSVC_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_external_service_conditions.json'
    CREATE_EXTSVC_CONDITION_URL = 'https://api.newrelic.com/v2/alerts_external_service_conditions/policies/'
    INFRA_CONDITIONS_URL = 'https://infra-api.newrelic.com/v2/alerts/conditions'
    CREATE_INFRA_CONDITION_URL = 'https://infra-api.newrelic.com/v2/alerts/conditions'
    ENTITY_CONDITIONS_URL = 'https://api.newrelic.com/v2/alerts_entity_conditions'
    ALERT_VIOLATIONS_URL = 'https://api.newrelic.com/v2/alerts_violations.json'


class EUEndpoints:

    GRAPHQL_URL = 'https://api.eu.newrelic.com/graphql'
    SHOW_APM_APP_URL = 'https://api.eu.newrelic.com/v2/applications/'
    GET_APM_APP_URL = 'https://api.eu.newrelic.com/v2/applications.json'
    GET_BROWSER_APP_URL = 'https://api.eu.newrelic.com/v2/browser_applications.json'
    SHOW_MOBILE_APP_URL = 'https://api.eu.newrelic.com/v2/mobile_applications/'
    SHOW_APM_KT_URL = 'https://api.eu.newrelic.com/v2/key_transactions/'
    GET_APM_KT_URL = 'https://api.eu.newrelic.com/v2/key_transactions.json'
    PUT_LABEL_URL = 'https://api.eu.newrelic.com/v2/labels.json'
    GET_DASHBOARDS_URL = 'https://api.eu.newrelic.com/v2/dashboards.json'
    SHOW_DASHBOARDS_URL = 'https://api.eu.newrelic.com/v2/dashboards/'
    DEL_DASHBOARDS_URL = 'https://api.eu.newrelic.com/v2/dashboards/'
    MONITORS_URL = 'https://synthetics.eu.newrelic.com/synthetics/api/v3/monitors/'
    MONITORS_LABEL_URL = 'https://synthetics.eu.newrelic.com/synthetics/api/v4/monitors/'
    INSIGHTS_URL = 'https://insights-api.eu.newrelic.com/v1/accounts/%s/query'
    SEC_CREDENTIALS_URL = 'https://synthetics.eu.newrelic.com/synthetics/api/v1/secure-credentials'
    ALERTS_CHANNEL_URL = 'https://api.eu.newrelic.com/v2/alerts_channels.json'
    ALERT_POLICIES_URL = 'https://api.eu.newrelic.com/v2/alerts_policies.json'
    ALERT_POLICY_CHANNELS_URL = 'https://api.eu.newrelic.com/v2/alerts_policy_channels.json'
    DEL_ALERTS_URL = 'https://api.eu.newrelic.com/v2/alerts_policies/'
    DEL_CHANNELS_URL = 'https://api.eu.newrelic.com/v2/alerts_channels/'
    GET_APP_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_conditions.json'
    APP_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_conditions/'
    CREATE_APP_CONDITION_URL = 'https://api.eu.newrelic.com/v2/alerts_conditions/policies/'
    GET_SYNTH_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_synthetics_conditions.json'
    CREATE_SYNTHETICS_CONDITION_URL = 'https://api.eu.newrelic.com/v2/alerts_synthetics_conditions/policies/'
    LOC_FAILURE_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_location_failure_conditions/policies/'
    NRQL_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_nrql_conditions.json'
    CREATE_NRQL_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_nrql_conditions/policies/'
    EXTSVC_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_external_service_conditions.json'
    CREATE_EXTSVC_CONDITION_URL = 'https://api.eu.newrelic.com/v2/alerts_external_service_conditions/policies/'
    INFRA_CONDITIONS_URL = 'https://infra-api.eu.newrelic.com/v2/alerts/conditions'
    CREATE_INFRA_CONDITION_URL = 'https://infra-api.eu.newrelic.com/v2/alerts/conditions'
    ENTITY_CONDITIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_entity_conditions'
    ALERT_VIOLATIONS_URL = 'https://api.eu.newrelic.com/v2/alerts_violations.json'
