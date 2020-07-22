import library.clients.monitorsclient as mc


# loads up monitors from an account and caches them
# main purpose is to get monitor_id by monitor_name
class AccountMonitors:
    account_monitors = {}

    def __init__(self, account_id, api_key):
        self.account_id = account_id
        self.api_key = api_key

    def load(self):
        all_monitors_def_json = mc.fetch_all_monitors(self.api_key)
        for monitor_def_json in all_monitors_def_json:
            self.account_monitors[monitor_def_json['name']] = monitor_def_json

    def get(self, monitor_name):
        if not self.account_monitors:
            self.load_monitors()
        if monitor_name in self.account_monitors:
            return self.account_monitors[monitor_name]
        return None
