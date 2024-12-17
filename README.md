[![New Relic Experimental header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Experimental.png)](https://opensource.newrelic.com/oss-category/#new-relic-experimental)

# nr-account-migration 
Python scripts for bulk migrating New Relic entities and configurations from one account to another.
The migration provides detailed logs and CSV status to track the migration process.
These scripts have been tested and used by a couple of customers for their account migration initiatives. 
The project is currently code complete and new releases will be made only for bug fixes and if any new features are requested. 

The following entities are supported:

Synthetics

- [x] Synthetic Monitors (Simple, Browser, Scripted Browser, API Test)
- [x] Synthetic Monitor Scripts (For Scripted Browser, API Test) 
- [x] Monitor Secure Credentials(param names only with dummy values for Scripted Browser and API Test)

Alert Policies

- [x] Alert Policies and related notification channels
- [x] Notification channels (tested for email, webhook, pagerduty, opsgenie) - credentials populated with dummy values

Alert Conditions as below. Target entities replaced wherever applicable and found in target account.
- [x] Synthetic Monitor Conditions
- [x] Synthetic Multi Location Conditions
- [x] APM App Conditions 
- [x] Browser App Conditions (ensure target app with similar name is running)
- [x] Mobile App Conditions 
- [x] Key Transaction Conditions
- [x] NRQL Conditions (migrated as is)
- [x] External Service Conditions 
- [x] Infrastructure Conditions (migrated as is)

Entity tags for the following entity types.
- [x] APM applications
- [x] Browser applications
- [x] Infrastructure hosts
- [x] Infrastructure integrations
- [x] Lambda functions
- [x] Mobile applications
- [x] Synthetic monitors
- [x] Synthetic secure credentials

Dashboards
- [x] Dashboards, including multi page dashboards

APM Settings
- [x] Apdex Configuration

## Installation
### Pre-requisites
- [x] Python 3
- [x] pip3 install requests
### Install
- [x] Download and unzip a release of nr-account-migration project  


## Getting Started

The table below lists the scripts that can be used for different migration and other use cases.

These scripts, in some cases, require sequential execution as they build the data necessary to migrate entities from one account to another.

The details for each script is provided in the next Usage section.


| No. | Use Case                   |             Scripts | 
| --- | -------------------------- | ------------------- | 
| 1.  | Migrate Monitors           | fetchmonitors.py :arrow_right: migratemonitors.py :arrow_right: migratetags.py | 
| 2.  | Migrate Alert policies     | fetchchannels.py(optional) :arrow_right: store_policies.py :arrow_right: migratepolicies.py | 
| 3.  | Migrate Alert conditions   | store_policies.py :arrow_right: migratepolicies.py :arrow_right: migrateconditions.py | 
| 4.  | Migrate Alert notifications | store_policies.py :arrow_right: migratepolicies.py :arrow_right: migrateconditions.py :arrow_right: migrate_notifications.py | 
| 5.  | Migrate APM Configurations | migrate_apm.py :arrow_right: migratetags.py |
| 6.  | Migrate Dashboards | migrate_dashboards.py :arrow_right: migratetags.py |
| 7.  | Update Monitors | updatemonitors.py | 
| 8.  | Delete Monitors | deletemonitors.py | 
| 9.  | Migrate Tags | migratetags.py |
| 10.  | Update Workload Golden Signals | wlgoldensignals.py |


The following entities and configurations can be migrated:



| Entity Type | Synthetics                   |
| ----------- | ------------------------- | 
- [x] Synthetic Monitors (Simple, Browser, Scripted Browser, API Test) 
- [x] Synthetic Monitor Scripts (For Scripted Browser, API Test) 
- [x] Monitor Secure Credentials(param names only with dummy values for Scripted Browser and API Test) 

| Config Type | Alert Policies                   |
| ----------- | ------------------------- | 

- [x] Alert Policies and related notification channels
- [x] Notification destinations, channels, and workflows (tested for email, webhook, pagerduty, opsgenie) - credentials populated with dummy values

| Config Type | Alert Conditions     |
| ----------- | -----------------    | 

Target entities replaced wherever applicable and found in target account.

- [x] Synthetic Monitor Conditions
- [x] Synthetic Multi Location Conditions
- [x] APM App Conditions 
- [x] Browser App Conditions (ensure target app with similar name is running)
- [x] Mobile App Conditions 
- [x] Key Transaction Conditions
- [x] NRQL Conditions (migrated as is)
- [x] External Service Conditions
- [x] Infrastructure Conditions (migrated as is) 


Other Entities

- [x] Dashboards

APM Configuration

- [x] Apdex Configuration

## Usage

There are two approaches to migrating. The first uses a single script [migrate_account.py](migrate_account.py) to orchestrate the migration of configuration for a whole (single) account. The second approach requires individual scripts to be called in a specific order; this is more flexible, but is also more time consuming. 

For the second approach, using standalone scripts, please see the [Individual Scripts](https://github.com/newrelic-experimental/nr-account-migration#individual-scripts) section below.

### Single orchestration script: migrate_account.py
The migrate_account.py script is used to migrate various components (such as monitors, alert policies, conditions, notifications, and tags) from a source New Relic account to a target New Relic account. The script can be run in different modes to perform specific steps of the migration process.

#### Command-Line Arguments
The script accepts the following command-line arguments to control its behavior:

`--cleanup`: Run the cleanup function before other steps.

`--step2`: Run only the migrate_step2 function.

**Warning:** cleanup removes almost all configuration from the target account, so use with caution.

#### Usage
To run the script with the default behavior (fetch and migrate_step1):

`python migrate_account.py`

To run the script with cleanup, fetch, and migrate_step1:

`python migrate_account.py --cleanup`

To run the script with only migrate_step2:

`python migrate_account.py --step2`

It is intended that fetch and migrate_step1 are run first. They migrate synthetic monitors.

Before running step2 the agents sending data to the New Relic source account must be reconfigured to send their data to the target account. Some of the migration steps require that entities are already reporting to the 

Step2 migrates alert policies, alert conditions, alert notification, dashboards, APM app_apdex_threshold, end_user_apdex_threshold, and enable_real_user_monitoring settings. It also migrates dashboards and APM entity tags.

#### Configuration
The script uses several configuration variables to specify the source and target accounts, API keys, regions, and other settings. These variables are defined in the script itself and can be modified as needed:
```
SRC_ACCT = '1234567'
SRC_API_KEY = 'NRAK-1234...'
SRC_REGION = 'us'
SRC_INSIGHTS_KEY = 'NRIQ-2345...'
TGT_ACCT = '9876543'
TGT_API_KEY = 'NRAK-9876...'
TGT_REGION = 'eu'
```

### Individual scripts

####  1) python3 fetchmonitors.py 

```
usage: fetchmonitors.py --sourceAccount SOURCEACCOUNT --region [ us (default) |eu ] --sourceApiKey SOURCEAPIKEY --insightsQueryKey INSIGHTSQUERYKEY --toFile TOFILE
```

Parameter        | Note
---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
sourceAccount    | Account to fetch monitors from
region           | Optional region us (default) or eu
sourceApiKey     | This should be a User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Synthetics
insightsQueryKey | must be supplied to fetch secure credentials from Insights for any monitors that ran in the past 7 days. Secure credentials fetching is skipped if this is not passed.
toFile           | should only be a file name e.g. soure-monitors.csv. It will always be created in output/ directory

**Storage:** The monitors fetched will be stored in _db/accountId/monitors/timeStamp_
**Windows Only:** Unzip scripts in as short a path as possible like c:/ in case there are really long monitor names resulting in storage paths greater than 260 characters. If needed the script attempts to handle such long names by mapping the name to a 32 char guid. The mapping if used is stored in windows_names.json and used by migratemonitors.py.


####  3) python3 fetchchannels.py (optional if you want to use --useLocal option during migratepolicies)
```
usage: fetchchannels.py  --sourceAccount SOURCEACCOUNT [--sourceApiKey SOURCEAPIKEY] --region [ us (default) |eu ]
```
Fetches alert channels and builds a dictionary mapping channels to policy_id.

The channels are stored in db/accountId/alert_policies/alert_channels.json

During migratepolicies the stored alert_channels can be used by passing --useLocal

####  4) python3 migratemonitors.py
```
usage: migratemonitors.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT  [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] --timeStamp TIMESTAMP [--useLocal]
```

Parameter     | Note
------------- | --------------------------------------------------------------------------------------------------------
fromFile      | Must contain monitor names one per line. The fetchentities.py script can be used to help generate this list of monitors.
sourceAccount | Account to fetch monitors from
sourceRegion  | Optional region us (default) or eu
sourceApiKey  | This should be a User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Synthetics
targetAccount | Account to migrate monitors to
targetRegion  | Optional region us (default) or eu
targetApiKey  | This should be a User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Synthetics
timeStamp     | must match the timeStamp generated in fetchmonitors , used when useLocal flag is passed
useLocal      | By default monitors are fetched from sourceAccount. A pre-fetched copy can be used by passing this flag

**useLocal:** The monitors will be picked up from db/sourceAccount/monitors/timeStamp

**Note:** Labels have been deprecated and replaced by tags. Please use migratetags.py to migrate tags between entities. **The migratemonitors.py script will no longer migrate labels** 

**Status:**

- output/sourceAccount_fromFile_targetAccount.csv

Comma separated status for each migrated monitor as below.

[NAME, STATUS, SCRIPT_STATUS, SCRIPT_MESSAGE, CHECK_COUNT, SEC_CREDENTIALS, CONDITION_STATUS, CONDITION_RESULT, LOCATION, NEW_MON_ID, ERROR]

**Note:** CHECK_COUNT and SEC_CREDENTIALS are only applicable for scripted monitors

A value of 0 CHECK_COUNT for scripted monitors indicates it has not run in the past 7 days.

####  5) python3 store_policies.py

```
usage: store_policies.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY
```
Saves all alert polices in db/\<sourceAccount\>/alert_policies/alert_policies.json and output/\<sourceAccount\>_policies.csv; the latter is required as input for migratepolicies.py as the --fromFile argument.


####  6) python3 migratepolicies.py
Preconditions: store_policies.py.
```
usage: migratepolicies.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] [--useLocal]
```

Parameter        | Note
---------------- | ------------------------------------------------------------------------------------------------------
fromFile         | must contain alert policy names one per line
fromFileEntities | must contain APM, Browser, or Mobile application names or IDs or APM KT names or IDs (not GUIDs)
sourceAccount    | Account to fetch monitors from
sourceRegion     | Optional region us (default) or eu
sourceApiKey     | User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Alerts
targetAccount    | Account to migrate policies to
targetRegion     | Optional region us (default) or eu
targetApiKey     | User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Alerts
useLocal         | By alert channels are fetched from sourceAccount. A pre-fetched copy can be used by passing this flag.

The script migrates alert policies to target account if not present in target account.

Any Notification channels assigned in source account will also be migrated if not present.

If alert policy is present then only notification channels are migrated if not present. If both are present then it will just assign matching target channels to matching target policy.

At least one of `fromFile` or `fromFileEntities` must be specified.

If `fromFile` is specified, it must contain alert policy names that should be
migrated, one per line.

If `fromFileEntities` is specified, it must contain APM, Browser, or Mobile
application names or IDs or APM Key Transaction names or IDs. In this context,
IDs are those used by the [ReST v2 APIs](https://rpm.newrelic.com/api/explore).
For each application or key transaction, the policies of all alert
"app conditions" targeting the application or key transaction will be will be
added to the list of policies to migrate.

In order to differentiate between APM, Browser, Mobile or APM KT names / IDs
(since their namespaces overlap), values must be prefixed with the following
prefixes.

Type                 | Prefix
-------------------- | ------------
APM application      | APM_APP
Browser application  | BROWSER_APP
Mobile application   | MOBILE_APP
APM key transaction  | APM_KT

If no prefix is specified, APM_APP is assumed. For example,

Example                       | Type
----------------------------- | --------------------------
Demo Telco App                | APM application name
APM_APP.Demo Telco App        | APM application name
123456789                     | APM application ID
BROWSER_APP.123456789         | Browser application ID
MOBILE_APP.Demo Telco iOS App | Mobile application name
APM_KT.Order phone            | APM key transaction name

The applications or key transactions are mapped to policies by mapping the
applications or key transactions to conditions and then those conditions to
policies. This mapping is produced by the [store_policy_entity_map.py](./store_policy_entity_map.py)
script. This mapping can be pre-generated by running the script directly since
the mapping process can take a while. The `useLocal` flag can be used to direct
the `migratepolicies` script to use the pre-generated copy. The
[ReST v2 application condition API](https://rpm.newrelic.com/api/explore/alerts_conditions/list)
is used to build the mapping. For this reason, only the listed entity types can
be migrated and GraphQL style entity GUIDs can not be used.

**Note:** Conditions for web transaction percentiles, or conditions targeting
labels (dynamic targeting), are not available via this API endpoint and
therefore will not be considered during mapping. For policies containing
only these types of app conditions, the policies must be identified manually
via the `fromFile`.

If both `fromFile` and `fromFileEntities` are specified, the set of policies
to move will be the union of both.

**Status:** sourceAccount_fromFileName_fromFileEntitiesName_targetAccount.csv with following status keys.

[NAME, POLICY_EXISTED, POLICY_CREATED, STATUS, ERROR, CHANNELS, PUT_CHANNELS]

####  7) python3 migrateconditions.py

**Preconditions:** migratemonitors(if migrating synthetic conditions) and migratepolicies.

Any target APM , Browser, Mobile apps and Key transactions must be migrated manually.

```
usage: migrateconditions.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] [--matchSourceState] [--synthetics --app_conditions --nrql_conditions --infra_conditions]
```

Parameter      | Note
-------------- | --------------------------------------------------
fromFile       | must contain alert policy names one per line
fromFileEntities | must contain APM, Browser, or Mobile application names or IDs or APM KT names or IDs (not GUIDs)
sourceAccount  | Account to fetch monitors from
sourceRegion   | Optional region us (default) or eu
sourceApiKey   | User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Alerts
targetAccount  | Account to migrate policies to
targetRegion   | Optional region us (default) or eu
targetApiKey   | User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Alerts
matchSourceState | Match alert condition enabled/disabled state from the source account in the target account. By default, all copied alert conditions are disabled in the target account.
synthetics     | Pass this flag to migrate synthetic conditions
app_conditions | Pass this flag to migrate alert conditions for APM, Browser apps, Key Transactions
nrql_conditions | Migrate nrql conditions in the alert policies
ext_svc_conditions | Migrate External Service conditions in the alert policies
infra_conditions | Migrate infrastructure conditions in the alert policies

This script loads sourceAlertPolicy and alertConditions.

It will migrate conditions only if targetAlertPolicy by same name can be loaded from targetAccount.

For a synthetic condition the targetMonitor with matching monitorName is looked up in the targetAccount using graphQL API.

If found that targetMonitor's monitorId is used for the synthetic condition and the condition is created in the targetAlertPolicy.

For APM app conditions app matching language and name is looked up.

For Browser app condition app matching name of type browser application is looked up. 

If found the matching target entities are set as entities in the target condition. 

See above for a description of `fromFileEntities` and how policies are resolved
from application and key transaction names or IDs. Note that even though
`fromFileEntities` contains application and key transaction names or IDs,
conditions associated with the resolved set of policies will still only be moved
if `--app_conditions` is specified.

**Warning:** Any condition will be skipped if a condition with same name and target is found in target policy. For conditions with multiple target entities : target entities are skipped if already found in a condition with same name.

**Status:** output/sourceAccount_fromFileName_fromFileEntitiesName_targetAccount_conditions.csv

####  8) python3 migrate_notifications.py (migrate destinations, channels, and workflows)


**Preconditions:** `store_policies`, `migratepolicies`, and `migrateconditions`.

```
usage: migrate_notifications.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY]
```


Parameter      | Note
-------------- | --------------------------------------------------
sourceAccount  | Account to fetch monitors from
sourceRegion   | Optional region us (default) or eu
sourceApiKey   | User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Alerts
targetAccount  | Account to migrate policies to
targetRegion   | Optional region us (default) or eu
targetApiKey   | User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Alerts

This script migrates notification destinations, channels, and workflows.

**Warning:** Note that supported destination types are:
1. DESTINATION_TYPE_EMAIL,
1. DESTINATION_TYPE_MOBILE_PUSH,
1. DESTINATION_TYPE_SLACK_LEGACY,
1. DESTINATION_TYPE_WEBHOOK


####  9) python3 migrate_apm.py (Migrate settings for APM apps)

Migrate APM Apdex configuration settings. **This no longer migrates labels.** Please use migratetags.py instead for tag migrations.
```
usage: migrate_apm.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --targetApiKey TARGETAPIKEY  [--settings]
```
##### Note: Ensure target apps are running or were running recently so that the target ids can be picked


####  10) python3 migrate_dashboards.py

```
usage: migrate_dashboards.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] [--accountMappingFile ACCOUNTMAPPINGFILE]
```

Migrate dashboards between accounts, including modifying queries to point to the new target account. The fetchentities.py script can help create the file to pass with fromFile.

Parameter     | Note
------------- | --------------------------------------------------------------------------------------------------------
fromFile      | Must contain dashboard names one per line. The fetchentities.py script can be used to help generate this list of dashboards.
sourceAccount | Account to fetch dashboards from
sourceRegion  | Optional region us (default) or eu
sourceApiKey  | This should be a User API Key for sourceAccount for a user with admin (or add on / custom role equivalent) access to Dashboards
targetAccount | Account to migrate monitors to
targetRegion  | Optional region us (default) or eu
targetApiKey  | This should be a User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Dashboards
accountMappingFile  | Map account ids to alternatives using a dictionary in a [JSON file](account_mapping.json). Useful when moving between regions, e.g. from the us to eu region.

####  11) python3 migratetags.py

```
usage: migratetags.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --targetApiKey TARGETAPIKEY [--apm --browser --dashboards --infrahost --infraint --lambda --mobile --securecreds --synthetics]
```

Migrate entity tags between entities with matching names and entity types. 

Parameter      | Note
-------------- | --------------------------------------------------
fromFile       | Must contain entity names one per line. The fetchentities.py script can help create this file.
sourceAccount  | Account to search for a matching source entity
sourceRegion   | Optional region us (default) or eu
sourceApiKey   | User API Key for sourceAccount 
targetAccount  | Account to search for a matching target entity
targetRegion   | Optional region us (default) or eu
targetApiKey   | User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Alerts
apm            | Pass this flag to migrate APM entity tags
browser        | Pass this flag to migrate Browser entity tags
dashboards     | Pass this flag to migrate Dashboard entity tags
infrahost      | Pass this flag to migrate Infrastructure host entity tags
infraint       | Pass this flag to migrate Infrastructure integration entity tags (including cloud integration entities)
lambda         | Pass this flag to migrate Lambda entity tags
mobile         | Pass this flag to migrate Mobile entity tags
securecreds    | Pass this flag to migrate Synthetic secure credential entity tags (tags only, not secure credentials themselves)
synthetics     | Pass this flag to migrate Synthetic monitor entity tags


####  12) python3 updatemonitors.py **Note:** Must use fetchmonitors before using updatemonitors

Potential use is for renaming/disabling migrated monitors in source account.

```
usage: updatemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --timeStamp TIMESTAMP [--renamePrefix RENAMEPREFIX] [--disable]
```

Parameter     | Note
------------- | -------------------------------------------------------------------------
fromFile      | Specifies the file with relative path, listing the monitors to be updated. The fetchentities.py script can help generate this file.
targetAccount | Account in which monitors need to be updated
targetRegion   | Optional region us (default) or eu
targetApiKey  | This should be a User API Key for targetAccount for a user with admin (or add on / custom role equivalent) access to Synthetics
timeStamp     | must match the timeStamp generated in fetchmonitors
renamePrefix  | Monitors are renamed with this prefix
disable       | Monitors are disabled

Supports two types of updates. Either of them or both must be specified.

- Rename monitor : e.g. --renamePrefix migrated_
- Disable monitor : e.g. --disable

**Status:**

output/targetAccount_fromFile_updated_monitors.csv

**Status keys:** [STATUS, UPDATED_NAME, UPDATED_STATUS, UPDATED_JSON, ERROR]

####  13) python3 fetchentities.py
```
usage: fetchentities.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY --toFile FILENAME [--tagName TAGNAME --tagValue TAGVALUE] [--apm --browser --dashboards --infrahost --infraint --lambda --mobile --securecreds --synthetics]
```
Create a file in the output directory that contains entity names from the source account. This can be filtered by using --tagName and --tagValue. This may be beneficial for other migration scripts in this repo that require a fromFile argument.

Parameter      | Note
-------------- | --------------------------------------------------
sourceAccount  | Account to search for matching entities
sourceRegion   | Optional region us (default) or eu
sourceApiKey   | User API Key for sourceAccount 
toFile         | File name to use to store entity names. This file will be created in the output directory.
tagName        | Tag name to use to filter results
tagValue       | Tag value to use to filter results
apm            | Pass this flag to list APM entities
browser        | Pass this flag to list Browser entities
dashboards     | Pass this flag to list Dashboard entities
infrahost      | Pass this flag to list Infrastructure host entities
infraint       | Pass this flag to list Infrastructure integration entities (including cloud integration entities)
lambda         | Pass this flag to list Lambda entities
mobile         | Pass this flag to list Mobile entities
securecreds    | Pass this flag to list Synthetic secure credential entities
synthetics     | Pass this flag to list Synthetic monitor entities
workload       | Pass this flag to list Workloads


####  14) python3 deletemonitors.py

```
usage: deletemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --timeStamp TIMESTAMP
```

Will delete monitors listed one per line in --fromFile and stored in db/targetaccount/monitors/timeStamp. The fetchentities.py script can help generate this file.

####  15) (optional Testing purpose only) python3 deleteallmonitors.py

#### Warning: All monitors in target account will be deleted

```
usage: deleteallmonitors.py [-h] [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION]
```

deleteallmonitors fetches all the monitors. Backs them up in db/accountId/monitors/timeStamp-bakup And deletes all the monitors

##### Note: In case this script is used in error use migratemonitors to restore the backed up monitors

####  16) (optional) python3 store_violations.py

```
usage: store_violations.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY --startDate STARTDATE --endDate ENDDATE [--onlyOpen]
```

 --sourceAccount SOURCEACCOUNT Source accountId

 --sourceRegion' SOURCEREGION us (default) or eu
 
  --sourceApiKey SOURCEAPIKEY Source account API Key or set environment variable ENV_SOURCE_API_KEY
  
  --startDate STARTDATE startDate format 2020-08-03T19:18:00+00:00
  
  --endDate ENDDATE     endDate format 2020-08-04T19:18:00+00:00
  
  --onlyOpen            By default all violations are fetched pass --onlyOpen to fetch only open violations
 

Saves all alert violations in db/<sourceAccount>/alert_violations/alert_violations.json
and db/<sourceAccount>/alert_violations/alert_violations.csv    

####  17) (optional) python3 store_policy_entity_map.py
```
usage: store_policy_entity_map.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY --useLocal
```
Builds a mapping from APM, Browser, and Mobile applications and APM key
transactions to and from alert policies for any policies which contain
"app conditions" as identified by the
[ReST v2 application condition API](https://rpm.newrelic.com/api/explore/alerts_conditions/list).

Saves the mapping in db/<sourceAccount>/alert_policies/alert_policy_entity_map.json


####  18) python3 nrmig
Configure appropriate [config.ini](config.ini.example) and run nrmig command.

`python3 nrmig -c ./config.ini migrate policies`

`python3 nrmig -c ./config.ini migrate conditions`


####  19) python3 fetchalldatatypes

--hostsFile should contain hostNames(entityNames) one per line. 

hostsFile can also be generated by using fetchentities script.
```
usage: fetchalldatatypes.py --hostsFile HOSTS_FILE --sourceAccount SOURCE_ACCOUNT_ID --sourceApiKey SOURCE_API_KEY --insightsQueryKey INSIGHTS_QUERY_KEY [--region NR_REGION]
```
output : output/<entityName>.csv file for each entityName with names of metrics and events 

received from that entity

####  20) python3 wlgoldensignals.py
Automated script for overriding and resetting golden signals for workloads. 
####Note: By default workloads only display 4 golden signals.
```
usage: wlgoldensignals.py --targetAccount TARGETACCOUNT --targetApiKey  TARGETAPIKEY [--targetRegion TARGETREGION] [--tagName TAGNAME] [--tagValue TAGVALUE] [--goldenSignalsJson GOLDENSIGNALSJSON] [--resetGoldenSignals] [--domain DOMAIN] [--type TYPE]
```
Parameter      | Note
-------------- | --------------------------------------------------
targetAccount  | Account containing the workloads
targetRegion   | Optional region us (default) or eu
targetApiKey   | User API Key for targetAccount
tagName        | Tag name to use to find matching workloads 
tagValue       | Tag value to use to find matching workloads
goldenSignalsJson     | File stored under ./goldensignals directory that contains list of metrics in JSON format. [./goldensignals/linuxgoldensignals.json](goldensignals/linuxgoldensignals.json)
resetGoldenSignals | Pass this flag to reset the override golden signals for a domain/type combination
domain | domain for which to reset the golden signals APM , BROWSER , INFRA , MOBILE , SYNTH , EXT
type | type of entity APPLICATION , DASHBOARD , HOST , MONITOR , WORKLOAD

#### example 1: override golden signals
python3 wlgoldensignals.py --targetAccount ACCT_ID --targetApiKey USER_API_KEY --goldenSignalsJson windowsgoldensignals.json --tagName Environment --tagValue WindowsProduction
The above will find workloads having tag Environment=WindowsProduction and then for each workload 
override the golden signals as specified in goldensignals/windowsgoldensignals.json for entities of domain INFRA and type HOST as specified in the json file

#### example 2: reset override golden signals
python3 wlgoldensignals.py --targetAccount ACCT_ID --targetApiKey USER_API_KEY --resetGoldenSignals --tagName Environment --tagValue WindowsProduction --domain INFRA --type HOST
The above will find workloads having tag Environment=WindowsProduction and then for each workload 
reset the golden signals for domain INFRA and type HOST


### Logging

Logs are stored in logs/migrate.log Logging level can be set in migrationlogger.py. Default level for file and stdout is INFO


## Testing

testall.py has system and miscellaneous test scripts. This test does require population of test data in a test account.
Verification of test is also manual at the moment.  


## Contributing
We encourage your contributions to improve nr-account-migration! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.
If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company,  please drop us an email at opensource@newrelic.com.

### Style Guide
Use PEP 8 Style Guide for Python Code https://www.python.org/dev/peps/pep-0008/

**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).

## License
nr-account-migration is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
