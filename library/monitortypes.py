
SIMPLE_BROWSER = 'BROWSER'
SCRIPTED_BROWSER = 'SCRIPT_BROWSER'
API_TEST = 'SCRIPT_API'
PING = 'SIMPLE'


def is_scripted(monitor):
    return monitor['type'] == SCRIPTED_BROWSER or monitor['type'] == API_TEST

def prep_ping(monitor):
    monitor['status'] = 'Disabled'
    if 'id' in monitor:
        del monitor['id']
    if 'modifiedAt' in monitor:
        del monitor['modifiedAt']
    if 'createdAt' in monitor:
        del monitor['createdAt']
    if 'userId' in monitor:
        del monitor['userId']
    if 'apiVersion' in monitor:
        del monitor['apiVersion']
    return monitor


def prep_simple_browser(monitor):
    monitor['status'] = 'Disabled'
    if 'id' in monitor:
        del monitor['id']
    if 'modifiedAt' in monitor:
        del monitor['modifiedAt']
    if 'createdAt' in monitor:
        del monitor['createdAt']
    if 'userId' in monitor:
        del monitor['userId']
    if 'apiVersion' in monitor:
        del monitor['apiVersion']
    if 'bypassHEADRequest' in monitor['options']:
        del monitor['options']['bypassHEADRequest']
    return monitor


def prep_scripted_browser(monitor):
    monitor['status'] = 'Disabled'
    if 'id' in monitor:
        del monitor['id']
    if 'modifiedAt' in monitor:
        del monitor['modifiedAt']
    if 'createdAt' in monitor:
        del monitor['createdAt']
    if 'userId' in monitor:
        del monitor['userId']
    if 'apiVersion' in monitor:
        del monitor['apiVersion']
    return monitor


def prep_api_test(monitor):
    monitor['status'] = 'Disabled'
    if 'id' in monitor:
        del monitor['id']
    if 'modifiedAt' in monitor:
        del monitor['modifiedAt']
    if 'createdAt' in monitor:
        del monitor['createdAt']
    if 'userId' in monitor:
        del monitor['userId']
    if 'apiVersion' in monitor:
        del monitor['apiVersion']
    return monitor


def prep_monitor_type(monitor):
    if monitor['type'] == 'BROWSER':
        return prep_simple_browser(monitor)
    elif monitor['type'] == 'SCRIPT_BROWSER':
        return prep_scripted_browser(monitor)
    elif monitor['type'] == 'SIMPLE':
        return prep_ping(monitor)
    elif monitor['type'] == 'SCRIPT_API':
        return prep_api_test(monitor)