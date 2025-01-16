from config import load_config

# Load the configuration
private_location_config = load_config('private_location_mapping.json')
public_location_config = load_config('public_location_mapping.json')
period_config = load_config('synthetic_period_mapping.json')

# Access the PRIVATE_LOCATION_MAP from the configuration
PRIVATE_LOCATION_MAP = private_location_config['PRIVATE_LOCATION_MAP']
# Access the PUBLIC_LOCATION_MAP from the configuration
PUBLIC_LOCATION_MAP = public_location_config['PUBLIC_LOCATION_MAP']
# Access the SYNTHETIC_PERIOD_MAP from the configuration
SYNTHETIC_PERIOD_MAP = period_config['SYNTHETIC_PERIOD_MAP']

# Define the monitor types
BROWSER = 'BROWSER'
SCRIPT_BROWSER = 'SCRIPT_BROWSER'
SCRIPT_API = 'SCRIPT_API'
SIMPLE = 'SIMPLE'
CERT_CHECK = 'CERT_CHECK'
BROKEN_LINKS = 'BROKEN_LINKS'
STEP_MONITOR = 'STEP_MONITOR'

# Define the monitor type function
SIMPLE_BROWSER_FUNCTION = 'syntheticsCreateSimpleBrowserMonitor'
SCRIPT_BROWSER_FUNCTION = 'syntheticsCreateScriptBrowserMonitor'
SCRIPT_API_FUNCTION = 'syntheticsCreateScriptApiMonitor'
SIMPLE_FUNCTION = 'syntheticsCreateSimpleMonitor'
CERT_CHECK_FUNCTION = 'syntheticsCreateCertCheckMonitor'
BROKEN_LINKS_FUNCTION = 'syntheticsCreateBrokenLinksMonitor'
STEP_MONITOR_FUNCTION = 'syntheticsCreateStepMonitor'

# Define the monitor input type
SIMPLE_BROWSER_INPUT_TYPE = 'SyntheticsCreateSimpleBrowserMonitorInput!'
SCRIPT_BROWSER_INPUT_TYPE = 'SyntheticsCreateScriptBrowserMonitorInput!'
SCRIPT_API_INPUT_TYPE = 'SyntheticsCreateScriptApiMonitorInput!'
SIMPLE_INPUT_TYPE = 'SyntheticsCreateSimpleMonitorInput!'
CERT_CHECK_INPUT_TYPE = 'SyntheticsCreateCertCheckMonitorInput!'
BROKEN_LINKS_INPUT_TYPE = 'SyntheticsCreateBrokenLinksMonitorInput!'
STEP_MONITOR_INPUT_TYPE = 'SyntheticsCreateStepMonitorInput!'


def is_scripted(monitor):
    return ('monitorType' in monitor and monitor['monitorType'] == SCRIPT_BROWSER) or ('type' in monitor and monitor['type'] == SCRIPT_BROWSER) or ('monitorType' in monitor and monitor['monitorType'] == SCRIPT_API) or ('type' in monitor and monitor['type'] == SCRIPT_API)


def is_step_monitor(monitor):
    return ('monitorType' in monitor and monitor['monitorType'] == STEP_MONITOR) or ('type' in monitor and monitor['type'] == STEP_MONITOR)


def prep_ping(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    custom_headers = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'customHeader']
    if custom_headers:
        custom_headers = custom_headers[0][0]
        custom_headers = { 'name': custom_headers.split(':')[0], 'value': custom_headers.split(':')[1] }
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    redirect_is_failure = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'redirectIsFailure'][0][0]
    response_validation_text = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'responseValidationText']
    response_validation_text = response_validation_text[0][0] if response_validation_text else None
    should_bypass_head_request = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'shouldBypassHeadRequest'][0][0]
    useTlsValidation = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'useTlsValidation'][0][0]
    # Create a dictionary with the monitor data
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
            'private': private_locations,
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
    custom_headers = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'customHeader']
    if custom_headers:
        custom_headers = custom_headers[0][0]
        custom_headers = { 'name': custom_headers.split(':')[0], 'value': custom_headers.split(':')[1] }
    devices = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'devices'), None)
    enableScreenshotOnFailureAndScript = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'enableScreenshotOnFailureAndScript'][0][0]
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    response_validation_text = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'responseValidationText']
    response_validation_text = response_validation_text[0][0] if response_validation_text else None
    runtime_type = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'][0][0]
    runtime_type_version = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'][0][0]
    script_language = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'][0][0]
    useTlsValidation = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'useTlsValidation'][0][0]
    # Create a dictionary with the monitor data
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
            'private': private_locations,
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
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
        # create a dict of the private locations using the key 'guid'
        private_locations = [{'guid': location} for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    script_language = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'), None)
    # Create a dictionary with the monitor data
    monitor_data = {
        'advancedOptions':
        {
            'enableScreenshotOnFailureAndScript': bool(enableScreenshotOnFailureAndScript),
        },
        'apdexTarget': float(apdex_target),
        'browsers': browsers,
        'devices': devices,
        'locations': {
            'private': private_locations,
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
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
        # create a dict of the private locations using the key 'guid'
        private_locations = [{'guid': location} for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    script_language = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'scriptLanguage'), None)
    # Create a dictionary with the monitor data
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
            'private': private_locations,
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': runtime,
        'script': monitor['script'],
        'status': 'DISABLED'
    }
    return monitor_data


def prep_cert_check(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    domain = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'domain'][0][0]
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
        # create a dict of the private locations using the key 'guid'
        private_locations = [{'guid': location} for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    number_days_to_fail_before_cert_expires = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'daysUntilExpiration'][0][0]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    # Create a dictionary with the monitor data
    if runtime_type:  # legacy monitors do not have runtime
        runtime = {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version
        }
    else:
        runtime = None
    monitor_data = {
        'apdexTarget': float(apdex_target),
        'domain': domain,
        'locations': {
            'private': private_locations,
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'numberDaysToFailBeforeCertExpires': int(number_days_to_fail_before_cert_expires),
        'period': period,
        'runtime': runtime,
        'status': 'DISABLED'
    }
    return monitor_data


def prep_broken_links(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
        # create a dict of the private locations using the key 'guid'
        private_locations = [{'guid': location} for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    # Create a dictionary with the api monitor data
    if runtime_type:  # legacy monitors do not have runtime
        runtime = {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version
        }
    else:
        runtime = None
    monitor_data = {
        'apdexTarget': float(apdex_target),
        'locations': {
            'private': private_locations,
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': runtime,
        'status': 'DISABLED',
        'uri': monitor['definition']['monitoredUrl']
    }
    return monitor_data


def prep_step(monitor):
    # Using list comprehension get the tag values with corresponding keys e.g. 'apdexTarget'
    apdex_target = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'apdexTarget'][0][0]
    browsers = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'browsers'), None)
    devices = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'devices'), None)
    enableScreenshotOnFailureAndScript = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'enableScreenshotOnFailureAndScript'][0][0]
    private_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'privateLocation'), [])
    if private_locations:
        # map the private location values using the private location map
        private_locations = [PRIVATE_LOCATION_MAP[location] for location in private_locations]
        # create a dict of the private locations using the key 'guid'
        private_locations = [{'guid': location} for location in private_locations]
    public_locations = next((tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'publicLocation'), [])
    if public_locations:
        # map the public location values using the public location map
        public_locations = [PUBLIC_LOCATION_MAP[location] for location in public_locations]
    period = [tag['values'] for tag in monitor['definition']['tags'] if tag['key'] == 'period'][0][0]
    # map the period values using the period map
    period = SYNTHETIC_PERIOD_MAP[period]
    runtime_type = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeType'), None)
    runtime_type_version = next((tag['values'][0] for tag in monitor['definition']['tags'] if tag['key'] == 'runtimeTypeVersion'), None)
    # Create a dictionary with the monitor data
    monitor_data = {
        'advancedOptions':
        {
            'enableScreenshotOnFailureAndScript': bool(enableScreenshotOnFailureAndScript),
        },
        'apdexTarget': float(apdex_target),
        'browsers': browsers,
        'devices': devices,
        'locations': {
            'private': private_locations,
            'public': public_locations
        },
        'name': monitor['definition']['name'],
        'period': period,
        'runtime': {
            'runtimeType': runtime_type,
            'runtimeTypeVersion': runtime_type_version
        },
        'status': 'DISABLED',
        'steps': monitor['steps']
    }
    return monitor_data


def prep_monitor_type(monitor):
    if ('type' in monitor['definition'] and monitor['definition']['type'] == BROWSER) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == BROWSER):
        return prep_simple_browser(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == SCRIPT_BROWSER) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == SCRIPT_BROWSER):
        return prep_scripted_browser(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == SIMPLE) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == SIMPLE):
        return prep_ping(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == SCRIPT_API) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == SCRIPT_API):
        return prep_api_test(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == CERT_CHECK) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == CERT_CHECK):
        return prep_cert_check(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == BROKEN_LINKS) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == BROKEN_LINKS):
        return prep_broken_links(monitor)
    elif ('type' in monitor['definition'] and monitor['definition']['type'] == STEP_MONITOR) or ('monitorType' in monitor['definition'] and monitor['definition']['monitorType'] == STEP_MONITOR):
        return prep_step(monitor)
