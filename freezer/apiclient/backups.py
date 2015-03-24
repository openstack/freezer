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

from freezer.freezerclient import exceptions


class BackupsManager(object):

    def __init__(self, client):
        self.client = client
        self.endpoint = self.client.endpoint + 'backups/'
        self.headers = {'X-Auth-Token': client.token}

    def create(self, backup_metadata, username=None, tenant_name=None):
        r = requests.post(self.endpoint,
                          data=json.dumps(backup_metadata),
                          headers=self.headers)
        if r.status_code != 201:
            raise exceptions.MetadataCreationFailure(
                "[*] Error {0}".format(r.status_code))
        backup_id = r.json()['backup_id']
        return backup_id

    def delete(self, backup_id, username=None, tenant_name=None):
        endpoint = self.endpoint + backup_id
        r = requests.delete(endpoint, headers=self.headers)
        if r.status_code != 204:
            raise exceptions.MetadataDeleteFailure(
                "[*] Error {0}".format(r.status_code))

    def list(self,  username=None, tenant_name=None):
        r = requests.get(self.endpoint, headers=self.headers)
        if r.status_code != 200:
            raise exceptions.MetadataGetFailure(
                "[*] Error {0}".format(r.status_code))

        return r.json()['backups']

    def get(self, backup_id, username=None, tenant_name=None):
        endpoint = self.endpoint + backup_id
        r = requests.get(endpoint, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.MetadataGetFailure(
            "[*] Error {0}".format(r.status_code))
