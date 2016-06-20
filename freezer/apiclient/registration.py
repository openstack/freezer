"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

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

from oslo_log import log

from freezer.apiclient import exceptions

LOG = log.getLogger(__name__)


class RegistrationManager(object):

    def __init__(self, client, verify=True):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/clients/'
        self.verify = verify

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, client_info):
        r = requests.post(self.endpoint,
                          data=json.dumps(client_info),
                          headers=self.headers,
                          verify=self.verify)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        client_id = r.json()['client_id']
        return client_id

    def delete(self, client_id):
        endpoint = self.endpoint + client_id
        r = requests.delete(endpoint, headers=self.headers,
                            verify=self.verify)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)

    def list(self, limit=10, offset=0, search=None):
        """
        Retrieves a list of client info structures

        :param limit: number of result to return (optional, default 10)
        :param offset: order of first document (optional, default 0)
        :param search: structured query (optional)
                       can contain:
                       * "match": list of {field, value}
                       Example:
                       { "match": [
                               {"description": "some search text here"},
                               {"client_id": "giano"},
                               ...
                             ],
                       }
        """
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data, verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['clients']

    def get(self, client_id):
        endpoint = self.endpoint + client_id
        r = requests.get(endpoint, headers=self.headers, verify=self.verify)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)
