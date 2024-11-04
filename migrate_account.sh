#!/bin/bash

# Note. Due to a limitation of the Synthetics REST API, which a number of the scripts use,
# the target API Key needs to belong to the target account.
# The GraphQL API doesn't have this limitation, but it is not currently used by the scripts.

SOURCE_ACCOUNT_ID=1234567  # Source account
SOURCE_ACCOUNT_REGION=us
SOURCE_API_KEY=NRAK-1234
SOURCE_INSIGHTS_QUERY_KEY=NRIQ-1234

TARGET_ACCOUNT_ID=9876543  # Target account
TARGET_ACCOUNT_REGION=eu
TARGET_API_KEY=NRAK-9876

# Step 1: Fetch the list of synthetics monitors from the source account
# The insights query key is required to fetch secure credentials (named correctly, but containing dummy values)
python3 fetchmonitors.py --sourceAccount $SOURCE_ACCOUNT_ID --region $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY  --insightsQueryKey $SOURCE_INSIGHTS_QUERY_KEY --toFile ${SOURCE_ACCOUNT_ID}_monitors.csv
SOURCE_MONITORS_TIMESTAMP=$(basename $(ls -td db/$SOURCE_ACCOUNT_ID/monitors/*/ | head -1))

# Step 1a: [Manual] Check for private location references and map in the private_location_mapping.json file

# Step 1b: Migrate monitors
python3 migratemonitors.py --fromFile output/${SOURCE_ACCOUNT_ID}_monitors.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --timeStamp $SOURCE_MONITORS_TIMESTAMP

# Step 1c: Migrate synthetic monitor tags
migratetags.py --fromFile output/${SOURCE_ACCOUNT_ID}_monitors.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --synthetics --securecreds

# Step 2: Store alert policies
python3 store_policies.py --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY

# Step 2a: Fetch alert channels
python3 fetchchannels.py --sourceAccount $SOURCE_ACCOUNT_ID --region $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY

# Step 2b: Migrate alert policies
python3 migratepolicies.py --fromFile output/${SOURCE_ACCOUNT_ID}_policies.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY

# Step 3: Migrate alert conditions
python3 migrateconditions.py --fromFile output/${SOURCE_ACCOUNT_ID}_policies.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --matchSourceState --synthetics --app_conditions --nrql_conditions --infra_conditions

# Step 4: Get APM entities
python3 fetchentities.py --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --toFile ${SOURCE_ACCOUNT_ID}_apm.csv --apm

#
# APM services, OTEL services, and Browser app settings need to be made now!
#

# Step 4a: Migrate APM app_apdex_threshold, end_user_apdex_threshold, and enable_real_user_monitoring settings
python3 migrate_apm.py --fromFile output/${SOURCE_ACCOUNT_ID}_apm.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY

# Step 4b: Migrate APM entity tags
python3 migratetags.py --fromFile output/${SOURCE_ACCOUNT_ID}_apm.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --apm

# Step 5: Fetch dashboards
python3 fetchentities.py --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --toFile ${SOURCE_ACCOUNT_ID}_dashboards.csv --dashboards

# Step 5a: Migrate dashboards
python3 migrate_dashboards.py --fromFile output/${SOURCE_ACCOUNT_ID}_dashboards.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY

# Step 5b: Migrate dashboard tags
python3 migratetags.py --fromFile output/${SOURCE_ACCOUNT_ID}_dashboards.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --dashboards

# Step 6: Fetch target account monitors
# Note. We are fetching the target account monitors, but using the source CLI options
python3 fetchmonitors.py --sourceAccount $TARGET_ACCOUNT_ID --region $TARGET_ACCOUNT_REGION --sourceApiKey $TARGET_API_KEY --toFile ${TARGET_ACCOUNT_ID}_monitors.csv
TARGET_MONITORS_TIMESTAMP=$(basename $(ls -td db/$SOURCE_ACCOUNT_ID/monitors/*/ | head -1))

# Step 6a: Disable source account monitors
# Note. We are updating the source account monitors, but using the target CLI options
# Note. Replace the timeStamp with the latest time for the source monitors
python3 updatemonitors.py --fromFile output/${SOURCE_ACCOUNT_ID}_monitors.csv --targetAccount $SOURCE_ACCOUNT_ID --targetRegion $SOURCE_ACCOUNT_REGION --targetApiKey $SOURCE_API_KEY --timeStamp $SOURCE_MONITORS_TIMESTAMP --disable

# Step 6b: Enable target account monitors
# Note. Replace the timeStamp with the latest time for the target monitors
python3 updatemonitors.py --fromFile output/${TARGET_ACCOUNT_ID}_monitors.csv --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --timeStamp $TARGET_MONITORS_TIMESTAMP --enable

# Step 7: Delete the source account monitors
# Note. We are updating the source account monitors, but using the target CLI options
python3 deletemonitors.py --fromFile output/${SOURCE_ACCOUNT_ID}_monitors.csv --targetAccount $SOURCE_ACCOUNT_ID --region $SOURCE_ACCOUNT_REGION --targetApiKey $SOURCE_API_KEY --timeStamp $SOURCE_MONITORS_TIMESTAMP

# Step 8: Fetch remaining entities for tagging
# e.g. for Lambda functions
python3 fetchentities.py --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --toFile ${SOURCE_ACCOUNT_ID}_lambda.csv --lambda

# Step 8a: Migrate remaining tags for other entity types
# e.g. for Lambda functions
python3 migratetags.py --fromFile output/${SOURCE_ACCOUNT_ID}_lambda.csv --sourceAccount $SOURCE_ACCOUNT_ID --sourceRegion $SOURCE_ACCOUNT_REGION --sourceApiKey $SOURCE_API_KEY --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY --lambda

# Step 9: Update Workload Golden Signals
# Note. Untested!
# python3 wlgoldensignals.py --targetAccount $TARGET_ACCOUNT_ID --targetRegion $TARGET_ACCOUNT_REGION --targetApiKey $TARGET_API_KEY [--tagName TAGNAME] [--tagValue TAGVALUE] [--goldenSignalsJson GOLDENSIGNALSJSON] [--resetGoldenSignals] [--domain DOMAIN] [--type TYPE]