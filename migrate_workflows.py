import os
import argparse
import fetchworkflows as fetchworkflows
import library.clients.notificationsclient as notificationsclient
import library.clients.workflowsclient as workflowsclient
import library.localstore as store
import library.migrationlogger as m_logger
import library.utils as utils


log = m_logger.get_logger(os.path.basename(__file__))
wc = workflowsclient.WorkflowsClient()


def print_args(args, src_api_key, src_region, tgt_api_key, tgt_region):
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])
    log.info("sourceRegion : " + src_region)
    log.info("Using targetAccount : " + str(args.targetAccount[0]))
    log.info("Using targetApiKey : " + len(tgt_api_key[:-4]) * "*" + tgt_api_key[-4:])
    log.info("targetRegion : " + tgt_region)


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate Workflows')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--targetAccount', nargs=1, type=int,  required=True, help='Target accountId')
    parser.add_argument('--targetApiKey', nargs=1, type=str, required=True, help='Target API Key, \
                                                                    or set environment variable ENV_TARGET_API_KEY')
    parser.add_argument('--targetRegion', type=str, nargs=1, required=False, help='targetRegion us(default) or eu')
    return parser


def create_workflow(workflow, tgt_acct, tgt_api_key, tgt_region):
    log.info(f"Creating workflow: {workflow['name']}")
    wc.create_workflow(workflow, tgt_api_key, tgt_acct, tgt_region)
    log.info(f"Created workflow: {workflow['name']}")


def migrate_workflows(src_acct, src_api_key, src_region, tgt_acct, tgt_api_key, tgt_region, channels_by_source_id, policies_by_source_id):
    log.info('Workflows migration started.')
    hasError = False
    workflows_by_source_id = fetchworkflows.fetch_workflows(src_api_key, src_acct, src_region)
    for workflow in workflows_by_source_id.values():
        log.info(f"Workflow name: {workflow['name']}")
        # Enrich destinationConfigurations with target channel ids
        log.info(f"Enriching destination configurations for target account: {tgt_acct}")
        if 'destinationConfigurations' in workflow:
            # Splice workflow['destinationConfigurations'] to contain only supported destinations
            workflow['destinationConfigurations'][:] = [destination_configuration for destination_configuration in workflow['destinationConfigurations'] if destination_configuration['type'] in notificationsclient.SUPPORTED_DESTINATIONS]
            if len(workflow['destinationConfigurations']) < 1:
                log.warning(f"Workflow name: {workflow['name']} does not contain a supported destination")
                continue
            for destination_configuration in workflow['destinationConfigurations']:
                if 'channelId' in destination_configuration:
                    source_channel_id = destination_configuration['channelId']
                    if source_channel_id in channels_by_source_id:
                        channel = channels_by_source_id.get(source_channel_id)
                        if 'targetChannelId' in channel:
                            destination_configuration['targetChannelId'] = channel['targetChannelId']
                            log.info(f"Target channel id: {destination_configuration['targetChannelId']} found for source channel id: {source_channel_id}")
                        else:
                            hasError = True
                            log.error(f"Unable to create workflow name: {workflow['name']}. Target channel id unavailable for source channel id: {source_channel_id} with type: {channel['type']}")
                    else:
                        hasError = True
                        log.error(f"Unable to create workflow name: {workflow['name']}. Source channel id: {source_channel_id} unavailable")
        else:
            hasError = True
            log.info(f"Workflow name: {workflow['name']} with id: {workflow['id']} has no destinationConfigurations: {workflow}")
        # Enrich issuesFilter with target account id and source policy ids
        log.info(f"Enriching issues filter for target account: {tgt_acct}")
        if "issuesFilter" in workflow:
            workflow['issuesFilter']['targetAccountId'] = int(tgt_acct)
            for predicate in workflow['issuesFilter']['predicates']:
                if predicate['attribute'] == 'labels.policyIds':
                    targetValues = []
                    for source_policy_id in predicate['values']:
                        if int(source_policy_id) in policies_by_source_id:
                            policy = policies_by_source_id.get(int(source_policy_id))
                            if 'targetPolicyId' in policy:
                                targetValues.append(str(policy['targetPolicyId']))
                                log.info(f"Target policy id: {str(policy['targetPolicyId'])} found for source policy id: {source_policy_id} ")
                            else:
                                hasError = True
                                log.error(f"Unable to create workflow name: {workflow['name']}. Target policy id unavailable for source policy id: {source_policy_id}")
                        else:
                            hasError = True
                            log.error(f"Unable to create workflow name: {workflow['name']}. Target policy id unavailable for source policy id: {source_policy_id}")
                    if len(targetValues) > 0:
                        predicate['targetValues'] = targetValues
                else:
                    log.debug(f"Ignoring predicate {predicate}")
        else:
            hasError = True
            log.info(f"Workflow name: {workflow['name']} with id: {workflow['id']} has no issuesFilter: {workflow}")
        # Create the workflow
        if not hasError:
            create_workflow(workflow, tgt_acct, tgt_api_key, tgt_region)
        else:
            log.error(f"Unable to create workflow name: {workflow['name']}, {workflow}")
    log.info('Workflows migration complete.')
    return channels_by_source_id


def main():
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    if not src_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    tgt_api_key = utils.ensure_target_api_key(args)
    if not tgt_api_key:
        utils.error_and_exit('target_api_key', 'ENV_TARGET_API_KEY')
    src_region = utils.ensure_source_region(args)
    tgt_region = utils.ensure_target_region(args)
    print_args(args, src_api_key, src_region, tgt_api_key, tgt_region)
    # TODO missing channels_by_source_id and policies_by_source_id arguments!
    migrate_workflows(args.sourceAccount[0], src_api_key, src_region, args.targetAccount[0], tgt_api_key, tgt_region)


if __name__ == '__main__':
    main()
