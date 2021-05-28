from pathlib import Path
import json
import os
import csv
from datetime import datetime
import library.monitortypes as monitortypes
import library.migrationlogger as migrationlogger
import library.windows_names as win_names
import library.utils as utils


# the fetched monitors are stored locally at db/<source_account>/monitors/<monitor_name>/<monitor_name>.json
DB_DIR = "db"
MONITORS_DIR = "monitors"
LABELS_DIR = "labels"
MONITOR_LABELS_FILE = "monitor_labels.json"
APM_LABELS_FILE = "apm_labels.json"
ALERT_POLICIES_DIR = "alert_policies"
ALERT_POLICIES_FILE = "alert_policies.json"
ALERT_POLICY_ENTITY_MAP_FILE = "alert_policy_entity_map.json"
ALERT_VIOLATIONS_DIR = "alert_violations"
ALERT_VIOLATIONS_FILE = "alert_violations.json"
ALERT_VIOLATIONS_CSV = "alert_violations.csv"
ALERT_CHANNELS_FILE = "alert_channels.json"
MONITOR_LABELS_CSV = "monitor_labels.csv"
SYNTHETIC_ALERTS_FILE = "synthetics_alerts.json"


logger = migrationlogger.get_logger(os.path.basename(__file__))


def create_storage_dirs(account_id, timestamp):
    logger.debug("Creating storage dirs")
    base_dir = Path("db")
    storage_dir = base_dir / account_id / "monitors" / timestamp
    storage_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(storage_dir))
    return storage_dir


def create_labels_dir(account_id):
    base_dir = Path("db")
    monitor_labels_dir = base_dir / account_id / LABELS_DIR
    monitor_labels_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(monitor_labels_dir))
    return monitor_labels_dir


def create_file(file_name):
    if file_name.exists():
        logger.info("Removing existing file " + file_name.name)
        os.remove(file_name)
    file_name.touch()
    if file_name.exists():
        logger.info("Created " + file_name.name)
    else:
        logger.error("Could not create " + file_name.name)
    return file_name


def save_monitor_labels(labels_dir, monitor_labels_json):
    monitor_labels_file = labels_dir / MONITOR_LABELS_FILE
    create_file(monitor_labels_file)
    monitor_labels_file.write_text(json.dumps(monitor_labels_json, indent=utils.DEFAULT_INDENT))


def apm_labels_location(acct_id):
    return DB_DIR + '/' + str(acct_id) + '/' + LABELS_DIR + '/' + APM_LABELS_FILE


def save_apm_labels(labels_dir, apm_labels_json):
    apm_labels_file = labels_dir / APM_LABELS_FILE
    create_file(apm_labels_file)
    apm_labels_file.write_text(json.dumps(apm_labels_json, indent=utils.DEFAULT_INDENT))


def save_monitor_labels_csv(monitor_labels_dir, monitor_labels_json):
    monitor_labels_csv = monitor_labels_dir / MONITOR_LABELS_CSV
    create_file(monitor_labels_csv)
    with open(str(monitor_labels_csv), 'w', newline='') as csvfile:
        labels_writer = csv.writer(csvfile, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for (monitor_id, labels) in monitor_labels_json.items():
            labels_writer.writerow([monitor_id] + labels)


def get_status_row(condition_status, statuskeys ):
    status_values = []
    for stat_key in statuskeys.KEYS:
        if stat_key in condition_status:
            status_values.append(condition_status[stat_key])
        else:
            status_values.append('NA')
    return status_values


def save_status_csv(status_file_name, condition_status_json, statuskeys):
    output_dir = Path("output")
    status_file = output_dir / status_file_name
    create_file(status_file)
    with open(str(status_file), 'w', newline='') as csvfile:
        status_writer = csv.writer(csvfile, delimiter=',',
                                   quotechar='"', quoting=csv.QUOTE_ALL)
        status_writer.writerow(['name'] + statuskeys.KEYS)  # header row
        for (name, status) in condition_status_json.items():
            status_writer.writerow([name] + get_status_row(status, statuskeys))


def load_names(from_file):
    names = []
    with open(from_file) as input_names:
        for monitor_name in input_names:
            names.append(monitor_name.rstrip().lstrip())
    return names


def load_script(monitor_dir, monitor):
    if monitortypes.is_scripted(monitor):
        script_file = monitor_dir / "script.json"
        if script_file.exists():
            monitor['script'] = json.loads(script_file.read_text())
        else:
            logger.error("Script file does not exist " + script_file.name)


def load_monitors(account_id, timestamp, monitor_names):
    monitors = []
    db_dir = Path(DB_DIR)
    monitors_dir = db_dir / str(account_id) / MONITORS_DIR / timestamp
    for monitor_name in monitor_names:
        monitor_json = load_monitor(monitors_dir, monitor_name)
        monitors.append(monitor_json)
    return monitors


def load_monitor(monitors_dir, monitor_name):
    adjusted_name = monitor_name
    if os.name == win_names.WINDOWS:
        adjusted_name = win_names.get_adjusted_name(monitors_dir, monitor_name)
    monitor_dir = monitors_dir / adjusted_name
    monitor_file_name = adjusted_name + ".json"
    monitor_file = monitor_dir / monitor_file_name
    monitor_json = json.loads(monitor_file.read_text())
    return monitor_json


def load_json_file(account_id, dir_name, json_file_name):
    file_json = {}
    db_dir = Path(DB_DIR)
    json_dir = db_dir / str(account_id) / dir_name
    if json_dir.exists():
        json_file = json_dir / json_file_name
        if json_file.exists():
            file_json = json.loads(json_file.read_text())
    return file_json


def load_monitor_labels(account_id):
    return load_json_file(account_id, LABELS_DIR, MONITOR_LABELS_FILE)


def load_apm_labels(account_id):
    return load_json_file(account_id, LABELS_DIR, APM_LABELS_FILE)


def load_synth_conditions(account_id):
    return load_json_file(account_id, ALERT_POLICIES_DIR, SYNTHETIC_ALERTS_FILE)


def load_alert_policies(account_id):
    return load_json_file(account_id, ALERT_POLICIES_DIR, ALERT_POLICIES_FILE)


def load_alert_policy_entity_map(account_id):
    return load_json_file(account_id, ALERT_POLICIES_DIR, ALERT_POLICY_ENTITY_MAP_FILE)


def load_alert_channels(account_id):
    return load_json_file(account_id, ALERT_POLICIES_DIR, ALERT_CHANNELS_FILE)


# creates and returns a file in the output directory
def create_output_file(file_name):
    logger.debug("Creating output file")
    output_dir = Path("output")
    output_dir.mkdir(mode=0o777, exist_ok=True)
    monitor_names_file = output_dir / file_name
    return create_file(monitor_names_file)


def sanitize(name):
    illegal_characters = ['/', '?', '<', '>', '\\', ':', '*', '|']
    characters = list(name)
    for index, character in enumerate(characters):
        if characters[index] in illegal_characters:
            characters[index] = '~'
    name = ''.join(characters)
    return name


def save_monitor_to_file(monitor_name, storage_dir, monitor_json):
    adjusted_name = monitor_name  # stays same for non-win and less than 260 char paths
    if os.name == win_names.WINDOWS:
        adjusted_name = win_names.adjust_monitor_name(monitor_name, storage_dir)
    if adjusted_name is not None:
        monitor_storage_dir = create_mon_storage_dir(adjusted_name, storage_dir)
        monitor_file = create_monitor_file(adjusted_name, monitor_storage_dir)
        monitor_file.write_text(json.dumps(monitor_json, indent=utils.DEFAULT_INDENT))


def create_mon_storage_dir(monitor_name, storage_dir):
    monitor_storage_dir = storage_dir / monitor_name
    monitor_storage_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    return monitor_storage_dir


def create_monitor_file(monitor_name, monitor_storage_dir):
    monitor_file_name = monitor_name + ".json"
    monitor_file = monitor_storage_dir / monitor_file_name
    monitor_file.touch()
    return monitor_file


def save_json(dir_path, file_name, dictionary):
    dir_path.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(dir_path))
    json_file = dir_path / file_name
    create_file(json_file)
    json_file.write_text(json.dumps(dictionary, indent=utils.DEFAULT_INDENT))


#  db/<account_id>/alert_policies/alert_policies.json
def save_alert_policies(account_id, alert_policies):
    base_dir = Path("db")
    alert_policies_dir = base_dir / account_id / ALERT_POLICIES_DIR
    save_json(alert_policies_dir, ALERT_POLICIES_FILE, alert_policies)


def save_alert_policy_entity_map(account_id, alert_policies_app_map):
    base_dir = Path("db")
    alert_policies_dir = base_dir / account_id / ALERT_POLICIES_DIR
    save_json(alert_policies_dir, ALERT_POLICY_ENTITY_MAP_FILE, alert_policies_app_map)


def save_alert_violations(account_id, alert_violations):
    base_dir = Path("db")
    alert_violations_dir = base_dir / account_id / ALERT_VIOLATIONS_DIR
    save_json(alert_violations_dir, ALERT_VIOLATIONS_FILE, alert_violations)


def save_alert_violations_csv(account_id, alert_violations_json):
    base_dir = Path("db")
    alert_violations_dir = base_dir / account_id / ALERT_VIOLATIONS_DIR
    alert_violations_csv = alert_violations_dir / ALERT_VIOLATIONS_CSV
    create_file(alert_violations_csv)
    with open(str(alert_violations_csv), 'w', newline='') as csvfile:
        violations_writer = csv.writer(csvfile, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)
        write_header = True
        for violation in alert_violations_json['violations']:
            if write_header:
                headers = violation.keys()
                violations_writer.writerow(headers)
                write_header = False
            violation = convert_timestamps_to_dates(violation)
            violations_writer.writerow(violation.values())


def convert_timestamps_to_dates(violation):
    opened_at_date = datetime.fromtimestamp(violation['opened_at']/1000)
    violation['opened_at'] = opened_at_date
    if 'closed_at' in violation:
        closed_at_date = datetime.fromtimestamp(violation['closed_at']/1000)
        violation['closed_at'] = closed_at_date
    return violation


#  db/<account_id>/alert_policies/alerts_channels.json
def save_alert_channels(account_id, all_alert_channels):
    base_dir = Path("db")
    alert_policies_dir = base_dir / account_id / ALERT_POLICIES_DIR
    save_json(alert_policies_dir, ALERT_CHANNELS_FILE, all_alert_channels)


#  db/<account_id>/alert_policies/synthetics_alerts.json
def save_synth_conditions(account_id, synth_conditions):
    base_dir = Path("db")
    alert_policies_dir = base_dir / account_id / ALERT_POLICIES_DIR
    save_json(alert_policies_dir, SYNTHETIC_ALERTS_FILE, synth_conditions)
