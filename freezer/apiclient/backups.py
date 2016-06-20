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


class BackupsManager(object):

    def __init__(self, client, verify=True):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/backups/'
        self.verify = verify

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, backup_metadata):
        if not backup_metadata.get('client_id', ''):
            backup_metadata['client_id'] = self.client.client_id
        r = requests.post(self.endpoint,
                          data=json.dumps(backup_metadata),
                          headers=self.headers,
                          verify=self.verify)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        backup_id = r.json()['backup_id']
        return backup_id

    def delete(self, backup_id):
        endpoint = self.endpoint + backup_id
        r = requests.delete(endpoint, headers=self.headers,
                            verify=self.verify)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)

    def list_all(self, limit=10, offset=0, search=None):
        """
        Retrieves a list of backups

        :param limit: number of result to return (optional, default 10)
        :param offset: order of first document (optional, default 0)
        :param search: structured query (optional)
                       can contain:
                       * "time_before": timestamp
                       * "time_after": timestamp
                       Example:
                       { "time_before": 1428529956 }
        """
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data, verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)

        return r.json()['backups']

    def list(self, limit=10, offset=0, search={}, client_id=None):
        client_id = client_id or self.client.client_id
        new_search = search.copy()
        new_search['match'] = search.get('match', [])
        new_search['match'].append({'client_id': client_id})
        return self.list_all(limit, offset, new_search)

    def get(self, backup_id):
        endpoint = self.endpoint + backup_id
        r = requests.get(endpoint, headers=self.headers, verify=self.verify)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)
