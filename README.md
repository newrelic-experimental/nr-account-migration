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

The table below lists the scripts that can be used for different migration use cases.

These scripts, in some cases, require sequential execution as they build the data necessary to migrate entities from one account to another.

The details for each script is provided in the next Usage section.


| No. | Use Case                   |             Scripts | 
| --- | -------------------------- | ------------------- | 
| 1.  | Migrate Monitors           | fetchmonitors.py :arrow_right: migratemonitors.py :arrow_right: migratetags.py | 
| 2.  | Migrate Alert policies     | fetchchannels.py(optional) :arrow_right: migratepolicies.py | 
| 3.  | Migrate Alert conditions   | migratepolicies.py :arrow_right: migrateconditions.py | 
| 4.  | Migrate APM Configurations | migrate_apm.py :arrow_right: migratetags.py |
| 5.  | Migrate Dashboards | migrate_dashboards.py :arrow_right: migratetags.py |
| 6.  | Update Monitors | updatemonitors.py | 
| 7.  | Delete Monitors | deletemonitors.py | 
| 8.  | Migrate Tags | migratetags.py


The following entities and configurations can be migrated:



| Entity Type | Synthetics                   |
| ----------- | ------------------------- | 
- [x] Synthetic Monitors (Simple, Browser, Scripted Browser, API Test) 
- [x] Synthetic Monitor Scripts (For Scripted Browser, API Test) 
- [x] Monitor Secure Credentials(param names only with dummy values for Scripted Browser and API Test) 

| Config Type | Alert Policies                   |
| ----------- | ------------------------- | 

- [x] Alert Policies and related notification channels
- [x] Notification channels (tested for email, webhook, pagerduty, opsgenie) - credentials populated with dummy values

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

####  1) python3 fetchmonitors.py 

```
usage: fetchmonitors.py --sourceAccount SOURCEACCOUNT --region [ us (default) |eu ]
                    --sourceApiKey SOURCEAPIKEY  
                    --insightsQueryKey INSIGHTSQUERYKEY
                    --toFile TOFILE
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

`usage: fetchchannels.py  --sourceAccount SOURCEACCOUNT [--sourceApiKey SOURCEAPIKEY] --region [ us (default) |eu ]`

Fetches alert channels and builds a dictionary mapping channels to policy_id.

The channels are stored in db/accountId/alert_policies/alert_channels.json

During migratepolicies the stored alert_channels can be used by passing --useLocal

####  4) python3 migratemonitors.py

`usage: migratemonitors.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT  [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] --timeStamp TIMESTAMP [--useLocal]`

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
useLocal      | By default monitors are fetched from sourceAccount. A pre-fetched copy can be used by passing this flag.

**useLocal:** The monitors will be picked up from db/sourceAccount/monitors/timeStamp

**Note:** Labels have been deprecated and replaced by tags. Please use migratetags.py to migrate tags between entities. **The migratemonitors.py script will no longer migrate labels** 

**Status:**

- output/sourceAccount_fromFile_targetAccount.csv

Comma separated status for each migrated monitor as below.

[NAME, STATUS, SCRIPT_STATUS, SCRIPT_MESSAGE, CHECK_COUNT, SEC_CREDENTIALS, CONDITION_STATUS, CONDITION_RESULT, LOCATION, NEW_MON_ID, ERROR]

**Note:** CHECK_COUNT and SEC_CREDENTIALS are only applicable for scripted monitors

A value of 0 CHECK_COUNT for scripted monitors indicates it has not run in the past 7 days.

####  5) python3 migratepolicies.py

`usage: migratepolicies.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] [--useLocal]`

Parameter        | Note
---------------- | ------------------------------------------------------------------------------------------------------
fromFile         | must contain alert policy names one per line
fromFileEntities | must contain APM, Browser, or Mobile application names or IDs or APM KT names or IDs (not GUIDs)
personalApiKey   | Personal API Key used for GraphQL API Client calls
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

####  6) python3 migrateconditions.py

**Preconditions:** migratemonitors(if migrating synthetic conditions) and migratepolicies.

Any target APM , Browser, Mobile apps and Key transactions must be migrated manually.

`usage: migrateconditions.py [-h] --fromFile FROMFILE --personalApiKey PERSONALAPIKEY --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] [--targetApiKey TARGETAPIKEY] [--matchSourceState] [--synthetics --app_conditions --nrql_conditions --infra_conditions]`

Parameter      | Note
-------------- | --------------------------------------------------
fromFile       | must contain alert policy names one per line
fromFileEntities | must contain APM, Browser, or Mobile application names or IDs or APM KT names or IDs (not GUIDs)
personalApiKey | Personal API Key used for GraphQL API Client calls
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

####  7) python3 migrate_apm.py (Migrate settings for APM apps)

Migrate APM Apdex configuration settings. **This no longer migrates labels.** Please use migratetags.py instead for tag migrations.

usage: migrate_apm.py --fromFile FROMFILE --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION] 
                        --personalApiKey PERSONALAPIKEY --sourceApiKey
                        SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] 
                        --targetApiKey TARGETAPIKEY  [--settings]

##### Note: Ensure target apps are running or were running recently so that the target ids can be picked


####  8) python3 migrate_dashboards.py

usage: migrate_dashboards.py [-h] --fromFile FROMFILE --sourceAccount [--sourceRegion SOURCEREGION] 
                             SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY
                             --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] 
                             [--targetApiKey TARGETAPIKEY]

Migrate dashboards between accounts, including modifying queries to point to the new target account. The fetchentities.py script can help create the file to pass with fromFile.

####  9) python3 migratetags.py

usage: migratetags.py [-h] --fromFile FROMFILE --sourceAccount
                            SOURCEACCOUNT [--sourceRegion SOURCEREGION] --sourceApiKey SOURCEAPIKEY
                            --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION]  --targetApiKey TARGETAPIKEY
                            [--apm --browser --dashboards --infrahost --infraint --lambda --mobile --securecreds --synthetics]

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


####  10) python3 updatemonitors.py **Note:** Must use fetchmonitors before using updatemonitors

Potential use is for renaming/disabling migrated monitors in source account.

`usage: updatemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --timeStamp TIMESTAMP [--renamePrefix RENAMEPREFIX] [--disable]`

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

####  11) python3 fetchentities.py

usage: fetchentities.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY
                            --toFile FILENAME [--tagName TAGNAME --tagValue TAGVALUE]
                            [--apm --browser --dashboards --infrahost --infraint --lambda --mobile --securecreds --synthetics] 

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


####  12) python3 deletemonitors.py

`usage: deletemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION] --timeStamp TIMESTAMP`

Will delete monitors listed one per line in --fromFile and stored in db/targetaccount/monitors/timeStamp. The fetchentities.py script can help generate this file.

####  13) (optional Testing purpose only) python3 deleteallmonitors.py

#### Warning: All monitors in target account will be deleted

`usage: deleteallmonitors.py [-h] [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT [--targetRegion TARGETREGION]`

deleteallmonitors fetches all the monitors. Backs them up in db/accountId/monitors/timeStamp-bakup And deletes all the monitors

##### Note: In case this script is used in error use migratemonitors to restore the backed up monitors

####  14) (optional) python3 store_policies.py

usage: store_policies.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY

Saves all alert polices in db/<sourceAccount>/alert_policies/alert_policies.json

####  15) (optional) python3 store_violations.py

usage: store_violations.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY --startDate STARTDATE --endDate ENDDATE [--onlyOpen]

 --sourceAccount SOURCEACCOUNT Source accountId

 --sourceRegion' SOURCEREGION us (default) or eu
 
  --sourceApiKey SOURCEAPIKEY Source account API Key or set environment variable ENV_SOURCE_API_KEY
  
  --startDate STARTDATE startDate format 2020-08-03T19:18:00+00:00
  
  --endDate ENDDATE     endDate format 2020-08-04T19:18:00+00:00
  
  --onlyOpen            By default all violations are fetched pass --onlyOpen to fetch only open violations
 

Saves all alert violations in db/<sourceAccount>/alert_violations/alert_violations.json
and db/<sourceAccount>/alert_violations/alert_violations.csv    

####  16) (optional) python3 store_policy_entity_map.py

usage: store_policy_entity_map.py [-h] --sourceAccount SOURCEACCOUNT [--sourceRegion SOURCEREGION]  --sourceApiKey SOURCEAPIKEY --useLocal

Builds a mapping from APM, Browser, and Mobile applications and APM key
transactions to and from alert policies for any policies which contain
"app conditions" as identified by the
[ReST v2 application condition API](https://rpm.newrelic.com/api/explore/alerts_conditions/list).

Saves the mapping in db/<sourceAccount>/alert_policies/alert_policy_entity_map.json


####  17) python3 nrmig
 Configure appropriate [config.ini](config.ini.example)  and run nrmig command 

 python3 nrmig -c ./config.ini migrate policies

 python3 nrmig -c ./config.ini migrate conditions
 
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