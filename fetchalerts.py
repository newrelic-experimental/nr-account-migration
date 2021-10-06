from pathlib import Path
import argparse
import os
import json
import library.localstore as store
import library.status.alertstatus as askeys
import library.migrationlogger as m_logger
import library.clients.alertsclient as ac
import library.utils as utils
import fetchchannels

# Migrates alert policy and assigned notification channels to targetAccount
# Alert Policy and Notification Channels are created only if not present in the targetAccount

log = m_logger.get_logger(os.path.basename(__file__))


def configure_parser():
    parser = argparse.ArgumentParser(description='Fetch alert related data')
    parser.add_argument('--sourceAccount', nargs=1, type=str, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--sourceRegion', type=str, nargs=1, required=False, help='sourceRegion us(default) or eu')
    parser.add_argument('--printConditionsFromFile', type=str, nargs=1, required=True, help='List of conditionIds')
    return parser


def print_args(args, src_api_key, src_region):
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))
    log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*" + src_api_key[-4:])
    log.info("sourceRegion : " + src_region)
    log.info("Using conditionsFromFile : " + args.printConditionsFromFile[0])


def print_matching_conditions(src_account, src_api_key, conditions_from_file, src_region):
    log.info('Loading condition IDs to fetch')
    condition_ids = store.load_names(conditions_from_file)
    log.info(json.dumps(condition_ids))
    log.info("Getting all alert policies")
    policies = ac.get_all_alert_policies(src_api_key, src_region)
    found_conditions = {}
    for policy in policies['policies']:
        #find_nrql_conditions(condition_ids, found_conditions, policy, src_account, src_api_key, src_region)
        find_infra_conditions(condition_ids, found_conditions, policy, src_api_key, src_region)
    if found_conditions:
        output_dir = Path("output")
        found_conditions_filename = src_account + "-foundConditions.json"
        store.save_json(output_dir, found_conditions_filename, found_conditions)
        log.info("Found Conditions also saved in output/"+ found_conditions_filename)
    else:
        log.info("No Conditions Found.")


def find_infra_conditions(condition_ids, found_conditions, policy, src_api_key, src_region):
    infra_conditions_by_id = ac.infra_conditions_by_id(src_api_key, policy['id'], src_region)
    if infra_conditions_by_id:
        condition_id_ints = list(map(int, condition_ids))
        for condition_id in condition_id_ints:
            if condition_id in infra_conditions_by_id:
                log.info("FOUND CONDITION " + str(condition_id))
                log.info("Policy : " + policy['name'] + "Condition : " + json.dumps(infra_conditions_by_id[condition_id]))
                found_conditions[condition_id] = infra_conditions_by_id[condition_id]
                found_conditions[condition_id]['policy_id'] = policy['id']
                found_conditions[condition_id]['policy_name'] = policy['name']
    else:
        log.info("No Infra conditions found in " + policy['name'])


def find_nrql_conditions(condition_ids, found_conditions, policy, src_account, src_api_key, src_region):
    log.info("Checking NRQL conditions in " + policy['name'])
    result = ac.nrql_conditions_by_id(src_api_key, src_account, policy['id'], src_region)
    if result['error']:
        log.error(result['error'])
        log.info("Checking remaining policies")
    elif result['conditions_by_id']:
        nrql_conditions_by_id = result['conditions_by_id']
        for condition_id in condition_ids:
            if condition_id in nrql_conditions_by_id:
                log.info("FOUND CONDITION " + condition_id)
                log.info(json.dumps(nrql_conditions_by_id[condition_id]))
                found_conditions[condition_id] = nrql_conditions_by_id[condition_id]
    else:
        log.info("No NRQL conditions found in " + policy['name'])


def main():
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    src_region = utils.ensure_source_region(args)
    if not src_api_key:
        utils.error_and_exit('source_api_key', 'ENV_SOURCE_API_KEY')
    print_matching_conditions(args.sourceAccount[0], src_api_key, args.printConditionsFromFile[0], src_region)


if __name__ == '__main__':
    main()
