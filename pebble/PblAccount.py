from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import Credentials
from oauth2client.file import Storage

import sys
import json
import collections
import datetime
import oauth2client.tools as tools
import argparse
import httplib2

AUTH_SERVER   = "https://auth.getpebble.com"
AUTHORIZE_URI = AUTH_SERVER + "/oauth/authorize"
TOKEN_URI     = AUTH_SERVER + "/oauth/token"

SDK_CLIENT_ID = "6c4f2bbb7553edf0cf93e12efc43468e8eee87e36f45903d2d65f9a43a5d44b2"
SDK_CLIENT_SECRET = "1d7cd5fea2696e86c6761f2c34d4e8dc10e35e7215171b0ad089e97de496a401"

flow = OAuth2WebServerFlow(
    client_id = SDK_CLIENT_ID,
    client_secret = SDK_CLIENT_SECRET,
    scope = "public",
    auth_uri = AUTHORIZE_URI,
    token_uri = TOKEN_URI
)

class PblAccount(object):
    def __init__(self, storage_file):
        self.storage = Storage(storage_file)

    def is_logged_in(self):
        return True if self.storage.get() else False

    def get_credentials(self):
        return self.storage.get()

    def get_token(self):
        return json.loads(self.storage.get().to_json())['access_token']

    def refresh_credentials(self):
        creds = self.get_credentials()
        if creds: creds.refresh(httplib2.Http())

    def get_access_token(self):
        creds = self.get_credentials()
        token_info = creds.get_access_token()
        return token_info.access_token

    # hack to fix null token expiration
    def set_expiration_to_long_time(self, creds):
        cred_str = creds.to_json()
        cred_json = json.loads(cred_str, object_pairs_hook=collections.OrderedDict)
        cred_json['token_expiry'] = '2100-01-01T00:00:01Z'
        cred_new_json = json.dumps(cred_json)
        return Credentials.new_from_json(cred_new_json)

    def login(self):
        parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        parser.set_defaults(auth_host_port = [60000])

        flags = parser.parse_args([])
        creds = self.set_expiration_to_long_time(tools.run_flow(flow, self.storage, flags))

        self.storage.put(creds)


def get_default_account(storage_file):
   return PblAccount(storage_file)

