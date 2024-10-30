from config import load_config

# Load the configuration
location_config = load_config('public_location_mapping.json')
period_config = load_config('synthetic_period_mapping.json')

# Access the PUBLIC_LOCATION_MAP from the configuration
PUBLIC_LOCATION_MAP = location_config['PUBLIC_LOCATION_MAP']
# Access the SYNTHETIC_PERIOD_MAP from the configuration
SYNTHETIC_PERIOD_MAP = period_config['SYNTHETIC_PERIOD_MAP']

# Define the monitor types
SIMPLE_BROWSER = 'BROWSER'
SCRIPTED_BROWSER = 'SCRIPT_BROWSER'
API_TEST = 'SCRIPT_API'
PING = 'SIMPLE'


def is_scripted(monitor):
    return monitor['monitorType'] == SCRIPTED_BROWSER or monitor['monitorType'] == API_TEST


def prep_ping(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    custom_headers = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'customHeader'][0][0]
    if custom_headers:
        custom_headers = { 'name': custom_headers.split(':')[0], 'value': custom_headers.split(':')[1] }
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    public_locations = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'][0]
    # map the public location values using the location map
    public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    redirect_is_failure = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'redirectIsFailure'][0][0]
    response_validation_text = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'responseValidationText'][0][0]
    should_bypass_head_request = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'shouldBypassHeadRequest'][0][0]
    useTlsValidation = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'useTlsValidation'][0][0]
    # Create a dictionary with the api monitor data
    monitor_data = {
        'apdexTarget': float(apdex_target),
        'advancedOptions': {
            'customHeaders': custom_headers,
            'redirectIsFailure': bool(redirect_is_failure),
            'responseValidationText': response_validation_text,
            'shouldBypassHeadRequest': bool(should_bypass_head_request),
            'useTlsValidation': bool(useTlsValidation)
        },
        'locations': {
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'status': 'DISABLED',
        'uri': monitor['definition']['monitoredUrl']
    }
    return monitor_data


def prep_simple_browser(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    browsers = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'browsers'), None)
    custom_headers = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'customHeader'][0][0]
    if custom_headers:
        custom_headers = { 'name': custom_headers.split(':')[0], 'value': custom_headers.split(':')[1] }
    devices = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'devices'), None)
    enableScreenshotOnFailureAndScript = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'enableScreenshotOnFailureAndScript'][0][0]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    public_locations = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'][0]
    # map the public location values using the location map
    public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    response_validation_text = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'responseValidationText'][0][0]
    runtime_type = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'][0][0]
    runtime_type_version = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'][0][0]
    script_language = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'][0][0]
    useTlsValidation = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'useTlsValidation'][0][0]
    # Create a dictionary with the api monitor data
    monitor_data = {
        'advancedOptions':
        {
            'customHeaders': custom_headers,
            'enableScreenshotOnFailureAndScript': bool(enableScreenshotOnFailureAndScript),
            'responseValidationText': response_validation_text,
            'useTlsValidation': bool(useTlsValidation)
        },
        'apdexTarget': float(apdex_target),
        'browsers': browsers,
        'devices': devices,
        'locations': {
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version,
            'scriptLanguage': script_language
        },
        'status': 'DISABLED',
        'uri': monitor['definition']['monitoredUrl']
    }
    return monitor_data


def prep_scripted_browser(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    browsers = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'browsers'), None)
    devices = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'devices'), None)
    enableScreenshotOnFailureAndScript = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'enableScreenshotOnFailureAndScript'][0][0]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    public_locations = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'][0]
    # map the public location values using the location map
    public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    script_language = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'), None)
    # Create a dictionary with the api monitor data
    monitor_data = {
        'advancedOptions':
        {
            'enableScreenshotOnFailureAndScript': bool(enableScreenshotOnFailureAndScript),
        },
        'apdexTarget': float(apdex_target),
        'browsers': browsers,
        'devices': devices,
        'locations': {
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version,
            'scriptLanguage': script_language
        },
        'script': monitor['script'],
        'status': 'DISABLED'
    }
    return monitor_data


def prep_api_test(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    # map the public location values using the location map
    public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    script_language = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'), None)
    # Create a dictionary with the api monitor data
    if runtime_type:  # legacy monitors do not have runtime
        runtime = {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version,
            'scriptLanguage': script_language
        }
    else:
        runtime = None
    monitor_data = {
        'apdexTarget': float(apdex_target),
        'locations': {
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': runtime,
        'script': monitor['script'],
        'status': 'DISABLED'
    }
    return monitor_data


def prep_monitor_type(monitor):
    if monitor['definition']['monitorType'] == 'BROWSER':
        return prep_simple_browser(monitor)
    elif monitor['definition']['monitorType'] == 'SCRIPT_BROWSER':
        return prep_scripted_browser(monitor)
    elif monitor['definition']['monitorType'] == 'SIMPLE':
        return prep_ping(monitor)
    elif monitor['definition']['monitorType'] == 'SCRIPT_API':
        return prep_api_test(monitor)