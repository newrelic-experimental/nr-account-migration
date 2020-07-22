import os
import json
import uuid
import library.migrationlogger as m_logger
import library.utils as utils
# stores adjusted monitors names when path exceeds 260 characters
WIN_NAMES_FILE = 'windows_names.json'
WINDOWS = 'nt'

log = m_logger.get_logger(os.path.basename(__file__))


# only adjusted on windows
# when path size exceeds 260 and switching name to a guid can reduce it to under that
def adjust_monitor_name(monitor_name, storage_dir):
    if os.name != WINDOWS:
        return monitor_name
    #  length of storage_dir/monitor_name/monitor_name.json
    storage_dir_len = len(str(storage_dir.resolve()))
    if (storage_dir_len + 2 * len(monitor_name) + 7) <= 260:
        return monitor_name
    windows_name = str(uuid.uuid4())
    if(storage_dir_len + 2 * len(windows_name) + 7) > 260:
        log.error('Unable to store as path size exceeds 260 even after adjusting the name to a guid: ' + monitor_name)
        return None
    save_windows_name(monitor_name, windows_name, storage_dir)
    log.warn('Due to long name, monitor name has been adjusted to: ' + windows_name)
    return windows_name


def get_adjusted_name(monitors_dir, monitor_name):
    if os.name != WINDOWS:
        return monitor_name
    storage_dir_len = len(str(monitors_dir.resolve()))
    if (storage_dir_len + 2 * len(monitor_name) + 7) <= 260:
        return monitor_name
    win_names_file = monitors_dir / WIN_NAMES_FILE
    if win_names_file.exists():
        win_names_json = json.loads(win_names_file.read_text())
        if monitor_name in win_names_json:
            return win_names_json[monitor_name]
        else:
            log.warn('The monitor may have not been fetched due to long name ' + monitor_name)
            return monitor_name


def save_windows_name(monitor_name, windows_name, storage_dir):
    win_names_file = storage_dir / WIN_NAMES_FILE
    if win_names_file.exists():
        win_names_json = json.loads(win_names_file.read_text())
        win_names_json[monitor_name] = windows_name
        win_names_file.write_text(json.dumps(win_names_json, indent=utils.DEFAULT_INDENT))
    else:
        win_names_file.touch()
        if win_names_file.exists():
            log.info('Created ' + str(win_names_file))
            win_names = {monitor_name: windows_name}
            win_names_file.write_text(json.dumps(win_names, indent=utils.DEFAULT_INDENT))
        else:
            log.error('Unable to Save windows names ' + win_names_file)