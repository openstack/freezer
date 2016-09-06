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


class JobManager(object):

    def __init__(self, client, verify=True):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/jobs/'
        self.verify = verify

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, doc, job_id=''):
        job_id = job_id or doc.get('job_id', '')
        endpoint = self.endpoint + job_id
        doc['client_id'] = doc.get('client_id', '') or self.client.client_id
        r = requests.post(endpoint,
                          data=json.dumps(doc),
                          headers=self.headers,
                          verify=self.verify)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        job_id = r.json()['job_id']
        return job_id

    def delete(self, job_id):
        endpoint = self.endpoint + job_id
        r = requests.delete(endpoint, headers=self.headers,
                            verify=self.verify)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)

    def list_all(self, limit=10, offset=0, search=None):
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data, verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['jobs']

    def list(self, limit=10, offset=0, search={}, client_id=None):
        client_id = client_id or self.client.client_id
        new_search = search.copy()
        new_search['match'] = search.get('match', [])
        new_search['match'].append({'client_id': client_id})
        return self.list_all(limit, offset, new_search)

    def get(self, job_id):
        endpoint = self.endpoint + job_id
        r = requests.get(endpoint, headers=self.headers, verify=self.verify)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)

    def update(self, job_id, update_doc):
        endpoint = self.endpoint + job_id
        r = requests.patch(endpoint,
                           headers=self.headers,
                           data=json.dumps(update_doc),
                           verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['version']

    def start_job(self, job_id):
        """
        Request to start a job

        :param job_id: the id of the job to start
        :return: the response obj:
                 {
                    result: string 'success' or 'already started'
                 }
        """
        # endpoint /v1/jobs/{job_id}/event
        endpoint = '{0}{1}/event'.format(self.endpoint, job_id)
        doc = {"start": None}
        r = requests.post(endpoint,
                          headers=self.headers,
                          data=json.dumps(doc),
                          verify=self.verify)
        if r.status_code != 202:
            raise exceptions.ApiClientException(r)
        return r.json()

    def stop_job(self, job_id):
        """
        Request to stop a job

        :param job_id: the id of the job to start
        :return: the response obj:
                 {
                    result: string 'success' or 'already stopped'
                 }
        """
        # endpoint /v1/jobs/{job_id}/event
        endpoint = '{0}{1}/event'.format(self.endpoint, job_id)
        doc = {"stop": None}
        r = requests.post(endpoint,
                          headers=self.headers,
                          data=json.dumps(doc),
                          verify=self.verify)
        if r.status_code != 202:
            raise exceptions.ApiClientException(r)
        return r.json()

    def abort_job(self, job_id):
        """
        Request to abort a job

        :param job_id: the id of the job to start
        :return: the response obj:
                 {
                    result: string 'success' or 'already stopped'
                 }
        """
        # endpoint /v1/jobs/{job_id}/event
        endpoint = '{0}{1}/event'.format(self.endpoint, job_id)
        doc = {"abort": None}
        r = requests.post(endpoint,
                          headers=self.headers,
                          data=json.dumps(doc),
                          verify=self.verify)
        if r.status_code != 202:
            raise exceptions.ApiClientException(r)
        return r.json()
