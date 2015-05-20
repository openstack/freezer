"""
Copyright 2015 Hewlett-Packard

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


class ActionManager(object):

    def __init__(self, client):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/actions/'

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, doc):
        r = requests.post(self.endpoint,
                          data=json.dumps(doc),
                          headers=self.headers)
        if r.status_code != 201:
            raise exceptions.MetadataCreationFailure(
                "[*] Error {0}: {1}".format(r.status_code, r.text))
        action_id = r.json()['action_id']
        return action_id

    def delete(self, action_id):
        endpoint = self.endpoint + action_id
        r = requests.delete(endpoint, headers=self.headers)
        if r.status_code != 204:
            raise exceptions.MetadataDeleteFailure(
                "[*] Error {0}".format(r.status_code))

    def list(self, limit=10, offset=0, search=None):
        """
        Retrieves a list of action info structures

        :param limit: number of result to return (optional, default 10)
        :param offset: order of first document (optional, default 0)
        :param search: structured query (optional)
                       can contain:
                       * "match": list of {field, value}
                       Example:
                       { "match": [
                               {"description": "some search text here"},
                               {"backup_name": "mydata"},
                               ...
                             ],
                       }
        """
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data)
        if r.status_code != 200:
            raise exceptions.MetadataGetFailure(
                "[*] Error {0}: {1}".format(r.status_code, r.text))
        return r.json()['actions']

    def get(self, action_id):
        endpoint = self.endpoint + action_id
        r = requests.get(endpoint, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.MetadataGetFailure(
            "[*] Error {0}".format(r.status_code))

    def update(self, action_id, update_doc):
        endpoint = self.endpoint + action_id
        r = requests.patch(endpoint,
                           headers=self.headers,
                           data=json.dumps(update_doc))
        if r.status_code != 200:
            raise exceptions.MetadataUpdateFailure(
                "[*] Error {0}: {1}".format(r.status_code, r.text))
        return r.json()['version']

    def set_status(self, action_id, new_status):
        return self.update(action_id, {'status': new_status})
