"""
Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================
"""

import json
import requests

from freezer.apiclient import exceptions


class ConfigsManager(object):

    def __init__(self, client):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/configs/'

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, config_file):
        r = requests.post(self.endpoint,
                          data=json.dumps(config_file),
                          headers=self.headers)
        if r.status_code != 201:
            raise exceptions.ConfigCreationFailure(
                "[*] Error {0}".format(r.status_code))
        config_id = r.json()['config_id']
        return config_id

    def delete(self, config_id):
        endpoint = self.endpoint + config_id
        r = requests.delete(endpoint, headers=self.headers)
        if r.status_code != 204:
            raise exceptions.ConfigDeleteFailure(
                "[*] Error {0}".format(r.status_code))

    def list(self, limit=10, offset=0, search=None):
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data)
        if r.status_code != 200:
            raise exceptions.ConfigGetFailure(
                "[*] Error {0}".format(r.status_code))

        return r.json()['configs']

    def get(self, config_id):
        endpoint = self.endpoint + config_id
        r = requests.get(endpoint, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ConfigGetFailure(
            "[*] Error {0}".format(r.status_code))

    def update(self, config_id, update_doc):
        endpoint = self.endpoint + config_id
        r = requests.patch(endpoint,
                           headers=self.headers,
                           data=json.dumps(update_doc))
        if r.status_code != 200:
            raise exceptions.ConfigUpdateFailure(
                "[*] Error {0}: {1}".format(r.status_code, r.text))
        return r.json()['version']
