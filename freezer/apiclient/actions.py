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

"""

import json
import requests

from freezer.apiclient import exceptions


class ActionManager(object):

    def __init__(self, client, verify=True):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/actions/'
        self.verify = verify

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, doc, action_id=''):
        action_id = action_id or doc.get('action_id', '')
        endpoint = self.endpoint + action_id
        r = requests.post(endpoint,
                          data=json.dumps(doc),
                          headers=self.headers,
                          verify=self.verify)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        action_id = r.json()['action_id']
        return action_id

    def delete(self, action_id):
        endpoint = self.endpoint + action_id
        r = requests.delete(endpoint,
                            headers=self.headers,
                            verify=self.verify)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)

    def list(self, limit=10, offset=0, search=None):
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data, verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['actions']

    def get(self, action_id):
        endpoint = self.endpoint + action_id
        r = requests.get(endpoint, headers=self.headers, verify=self.verify)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)

    def update(self, action_id, update_doc):
        endpoint = self.endpoint + action_id
        r = requests.patch(endpoint,
                           headers=self.headers,
                           data=json.dumps(update_doc), verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['version']
