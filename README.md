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
- [x] Monitor Labels

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
- [x] NRQL conditions (migrated as is)
- [x] External Service Conditions 


- [x] Synthetic Labels (migrated as Tags)


- [x] Dashboards

APM Settings
- [x] APM Labels
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
| 1.  | Migrate Monitors           | fetchmonitors.py :arrow_right: fetchlabels.py :arrow_right: migratemonitors.py | 
| 2.  | Migrate Alert policies     | fetchchannels.py(optional) :arrow_right: migratepolicies.py | 
| 3.  | Migrate Alert conditions   | migratepolicies.py :arrow_right: migrateconditions.py | 
| 4.  | Migrate APM Configurations | migrate_apm.py |
| 5.  | Migrate Dashboards | migrate_dashboards.py |
| 6.  | Update Monitors | updatemonitors.py | 
| 7.  | Delete Monitors | deletemonitors.py | 


The following entities and configurations can be migrated:



| Entity Type | Synthetics                   |
| ----------- | ------------------------- | 
- [x] Synthetic Monitors (Simple, Browser, Scripted Browser, API Test) 
- [x] Synthetic Monitor Scripts (For Scripted Browser, API Test) 
- [x] Monitor Secure Credentials(param names only with dummy values for Scripted Browser and API Test) 
- [x] Monitor Labels 

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
- [x] NRQL conditions (migrated as is)
- [x] External Service Conditions 


Other Entities

- [x] Dashboards

APM Configuration

- [x] APM Labels
- [x] Apdex Configuration

## Usage

####  1) python3 fetchmonitors.py 

```
usage: fetchmonitors.py [-h] --sourceAccount SOURCEACCOUNT
                    --sourceApiKey SOURCEAPIKEY  
                    --insightsQueryKey INSIGHTSQUERYKEY
                    --toFile TOFILE
```

Parameter        | Note
---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
sourceAccount    | Account to fetch monitors from
sourceApiKey     | This should be the Admin API Key for sourceAccount
insightsQueryKey | must be supplied to fetch secure credentials from Insights for any monitors that ran in the past 7 days. Secure credentials fetching is skipped if this is not passed.
toFile           | should only be a file name e.g. soure-monitors.csv. It will always be created in output/ directory

**Storage:** The monitors fetched will be stored in _db/accountId/monitors/timeStamp_
**Windows Only:** Unzip scripts in as short a path as possible like c:/ in case there are really long monitor names resulting in storage paths greater than 260 characters. If needed the script attempts to handle such long names by mapping the name to a 32 char guid. The mapping if used is stored in windows_names.json and used by migratemonitors.py.


####  2) python3 fetchlabels.py
Recommended to migrate synthetic monitor and APM application labels. 

`usage: fetchlabels.py [-h] --sourceAccount SOURCEACCOUNT [--sourceApiKey SOURCEAPIKEY]`

Fetches all labels and stores them indexed by monitor_id and app_id 

**Output:**

db/sourceAccount/monitor_labels/monitor_labels.json

db/sourceAccount/monitor_labels/monitor_labels.csv

db/sourceAccount/monitor_labels/apm_labels.json

**Note:** If present the monitor_labels file is used to apply labels when monitors are migrated from sourceAccount to another targetAccount.

###  3) python3 fetchchannels.py (optional if you want to use --useLocal option during migratepolicies)

`usage: fetchalerts.py [-h] --sourceAccount SOURCEACCOUNT [--sourceApiKey SOURCEAPIKEY]`

Fetches alert channels and builds a dictionary mapping channels to policy_id.

The channels are stored in db/accountId/alert_policies/alert_channels.json

During migratepolicies the stored alert_channels can be used by passing --useLocal

####  4) python3 migratemonitors.py

`usage: migratemonitors.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetApiKey TARGETAPIKEY] --timeStamp TIMESTAMP [--useLocal]`

Parameter     | Note
------------- | --------------------------------------------------------------------------------------------------------
fromFile      | must contain monitor names one per line
sourceAccount | Account to fetch monitors from
sourceApiKey  | This should be the Admin API Key for sourceAccount
targetAccount | Account to migrate monitors to
targetApiKey  | This should be the Admin API Key for targetAccount
personalApiKey | Personal API Key used for GraphQL API Client calls (required to apply tags)
timeStamp     | must match the timeStamp generated in fetchmonitors , used when useLocal flag is passed
useLocal      | By default monitors are fetched from sourceAccount. A pre-fetched copy can be used by passing this flag.

**useLocal:** The monitors will be picked up from db/sourceAccount/monitors/timeStamp

**Labels:** Any labels will be picked up from db/sourceAccount/monitor_labels if pre-fetched using fetchlabels

**Note:** Synthetic Labels are migrated as tags

**Status:**

- output/sourceAccount_fromFile_targetAccount.csv

Comma separated status for each migrated monitor as below.

[NAME, STATUS, SCRIPT_STATUS, SCRIPT_MESSAGE, CHECK_COUNT, SEC_CREDENTIALS, CONDITION_STATUS, CONDITION_RESULT, LOCATION, NEW_MON_ID, ERROR, LABELS]

**Note:** CHECK_COUNT and SEC_CREDENTIALS are only applicable for scripted monitors

A value of 0 CHECK_COUNT for scripted monitors indicates it has not run in the past 7 days.

####  5) python3 migratepolicies.py

`usage: migratepolicies.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetApiKey TARGETAPIKEY] [--useLocal]`

Parameter     | Note
------------- | ------------------------------------------------------------------------------------------------------
fromFile      | must contain alert policy names one per line
sourceAccount | Account to fetch monitors from
sourceApiKey  | Admin API Key for sourceAccount
targetAccount | Account to migrate policies to
targetApiKey  | Admin API Key for targetAccount
useLocal      | By alert channels are fetched from sourceAccount. A pre-fetched copy can be used by passing this flag.

The script migrates alert policies to target account if not present in target account.

Any Notification channels assigned in source account will also be migrated if not present.

If alert policy is present then only notification channels are migrated if not present. If both are present then it will just assign matching target channels to matching target policy.

**Status:** sourceAccount_fromFileName_targetAccount.csv with following status keys.

[NAME, POLICY_EXISTED, POLICY_CREATED, STATUS, ERROR, CHANNELS, PUT_CHANNELS]

####  6) python3 migrateconditions.py

**Preconditions:** migratemonitors(if migrating synthetic conditions) and migratepolicies.

Any target APM , Browser, Mobile apps and Key transactions must be migrated manually.

`usage: migrateconditions.py [-h] --fromFile FROMFILE --personalApiKey PERSONALAPIKEY --sourceAccount SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY --targetAccount TARGETACCOUNT [--targetApiKey TARGETAPIKEY] [--synthetics --apm_conditions --nrql_conditions]`

Parameter      | Note
-------------- | --------------------------------------------------
fromFile       | must contain alert policy names one per line
personalApiKey | Personal API Key used for GraphQL API Client calls
sourceAccount  | Account to fetch monitors from
sourceApiKey   | Admin API Key for sourceAccount
targetAccount  | Account to migrate policies to
targetApiKey   | Admin API Key for targetAccount
synthetics     | Pass this flag to migrate synthetic conditions
app_conditions | Pass this flag to migrate alert conditions for APM, Browser apps, Key Transactions
nrql_conditions | Migrate nrql conditions in the alert policies
ext_svc_conditions | Migrate External Service conditions in the alert policies


This script loads sourceAlertPolicy and alertConditions.

It will migrate conditions only if targetAlertPolicy by same name can be loaded from targetAccount.

For a synthetic condition the targetMonitor with matching monitorName is looked up in the targetAccount using graphQL API.

If found that targetMonitor's monitorId is used for the synthetic condition and the condition is created in the targetAlertPolicy.

For APM app conditions app matching language and name is looked up.

For Browser app condition app matching name of type browser application is looked up. 

If found the matching target entities are set as entities in the target condition. 

**Warning:** Any condition will be skipped if a condition with same name and target is found in target policy. For conditions with multiple target entities : target entities are skipped if already found in a condition with same name.

**Status:** output/sourceAccount_fromFile_targetAccount_conditions.csv

####  7) python3 migrate_apm.py (Migrate labels and settings for APM apps)

Migrate APM Apdex configuration settings and/or labels.

Pre-requisite step for migrating labels : fetchlabels.py

usage: migrate_apm.py [-h] --fromFile FROMFILE --sourceAccount SOURCEACCOUNT
                        --personalApiKey PERSONALAPIKEY --sourceApiKey
                        SOURCEAPIKEY --targetAccount TARGETACCOUNT
                        --targetApiKey TARGETAPIKEY  [--settings] [--labels]

##### Note: Ensure target apps are running or were running recently so that the target ids can be picked


####  8) python3 migrate_dashboards.py

usage: migrate_dashboards.py [-h] --fromFile FROMFILE --sourceAccount
                             SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY
                             --targetAccount TARGETACCOUNT
                             [--targetApiKey TARGETAPIKEY]


####  9) python3 updatemonitors.py **Note:** Must use fetchmonitors before using updatemonitors

Potential use is for renaming/disabling migrated monitors in source account.

`usage: updatemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT --timeStamp TIMESTAMP [--renamePrefix RENAMEPREFIX] [--disable]`

Parameter     | Note
------------- | -------------------------------------------------------------------------
fromFile      | specifies the file with relative path, listing the monitors to be updated
targetAccount | Account in which monitors need to be updated
targetApiKey  | This should be the Admin API Key for targetAccount
timeStamp     | must match the timeStamp generated in fetchmonitors
renamePrefix  | Monitors are renamed with this prefix
disable       | Monitors are disabled

Supports two types of updates. Either of them or both must be specified.

- Rename monitor : e.g. --renamePrefix migrated_
- Disable monitor : e.g. --disable

**Status:**

output/targetAccount_fromFile_updated_monitors.csv

**Status keys:** [STATUS, UPDATED_NAME, UPDATED_STATUS, UPDATED_JSON, ERROR]

####  10) python3 deletemonitors.py

`usage: deletemonitors.py [-h] --fromFile FROMFILE [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT --timeStamp TIMESTAMP`

Will delete monitors listed one per line in --fromFile and stored in db/targetaccount/monitors/timeStamp

####  11) (optional Testing purpose only) python3 deleteallmonitors.py

#### Warning: All monitors in target account will be deleted

`usage: deleteallmonitors.py [-h] [--targetApiKey TARGETAPIKEY] --targetAccount TARGETACCOUNT`

deleteallmonitors fetches all the monitors. Backs them up in db/accountId/monitors/timeStamp-bakup And deletes all the monitors

##### Note: In case this script is used in error use migratemonitors to restore the backed up monitors

####  12) (optional) python3 store_policies.py

usage: store_policies.py [-h] --sourceAccount SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY

Saves all alert polices in db/<sourceAccount>/alert_policies/alert_policies.json

####  13) (optional) python3 store_violations.py

usage: store_violations.py [-h] --sourceAccount SOURCEACCOUNT --sourceApiKey SOURCEAPIKEY --startDate STARTDATE --endDate ENDDATE [--onlyOpen]

 --sourceAccount SOURCEACCOUNT Source accountId
 
  --sourceApiKey SOURCEAPIKEY Source account API Key or set environment variable ENV_SOURCE_API_KEY
  
  --startDate STARTDATE startDate format 2020-08-03T19:18:00+00:00
  
  --endDate ENDDATE     endDate format 2020-08-04T19:18:00+00:00
  
  --onlyOpen            By default all violations are fetched pass --onlyOpen to fetch only open violations
 

Saves all alert violations in db/<sourceAccount>/alert_violations/alert_violations.json
and db/<sourceAccount>/alert_violations/alert_violations.csv    

### Logging

Logs are stored in logs/migrate.log Logging level can be set in migrationlogger.py. Default level for file and stdout is INFO


## Testing

testall.py has system and miscellaneous test scripts. This test does require population of test data in a test account.
Verification of test is also manual at the moment.  


## Contributing
We encourage your contributions to improve nr-account-migration! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.
If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company,  please drop us an email at opensource@newrelic.com.

**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).

## License
nr-account-migration is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
