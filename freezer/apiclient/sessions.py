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


class SessionManager(object):

    def __init__(self, client, verify=True):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/sessions/'
        self.verify = verify

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, doc, session_id=''):
        session_id = session_id or doc.get('session_id', '')
        endpoint = self.endpoint + session_id
        r = requests.post(endpoint,
                          data=json.dumps(doc),
                          headers=self.headers,
                          verify=self.verify)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        session_id = r.json()['session_id']
        return session_id

    def delete(self, session_id):
        endpoint = self.endpoint + session_id
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
        return r.json()['sessions']

    def list(self, limit=10, offset=0, search={}):
        new_search = search.copy()
        new_search['match'] = search.get('match', [])
        return self.list_all(limit, offset, new_search)

    def get(self, session_id):
        endpoint = self.endpoint + session_id
        r = requests.get(endpoint, headers=self.headers, verify=self.verify)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)

    def update(self, session_id, update_doc):
        endpoint = self.endpoint + session_id
        r = requests.patch(endpoint,
                           headers=self.headers,
                           data=json.dumps(update_doc),
                           verify=self.verify)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)
        return r.json()['version']

    def add_job(self, session_id, job_id):
        # endpoint /v1/sessions/{sessions_id}/jobs/{job_id}
        endpoint = '{0}{1}/jobs/{2}'.format(self.endpoint, session_id, job_id)
        r = requests.put(endpoint,
                         headers=self.headers, verify=self.verify)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)
        return

    def remove_job(self, session_id, job_id):
        # endpoint /v1/sessions/{sessions_id}/jobs/{job_id}
        endpoint = '{0}{1}/jobs/{2}'.format(self.endpoint, session_id, job_id)
        retry = 5
        r = ''
        while retry:
            r = requests.delete(endpoint,
                                headers=self.headers, verify=self.verify)
            if r.status_code == 204:
                return
            retry -= 1
        raise exceptions.ApiClientException(r)

    def start_session(self, session_id, job_id, session_tag):
        """
        Informs the api that the client is starting the session
        identified by the session_id and request the session_tag
        to be incremented up to the requested value.
        The returned session_id could be:
         * current_tag + 1 if the session has started
         * > current_tag + 1 if the action had already been started
           by some other node and this node was out of sync

        :param session_id:
        :param job_id:
        :param session_tag: the new session_id
        :return: the response obj:
                 { result: string 'running' or 'error',
                  'session_tag': the new session_tag )
        """
        # endpoint /v1/sessions/{sessions_id}/action
        endpoint = '{0}{1}/action'.format(self.endpoint, session_id)
        doc = {"start": {
            "job_id": job_id,
            "current_tag": session_tag
            }}
        r = requests.post(endpoint,
                          headers=self.headers,
                          data=json.dumps(doc),
                          verify=self.verify)
        if r.status_code != 202:
            raise exceptions.ApiClientException(r)
        return r.json()

    def end_session(self, session_id, job_id, session_tag, result):
        """
        Informs the freezer service that the job has ended.
        Provides information about the job's result and the session tag

        :param session_id:
        :param job_id:
        :param session_tag:
        :param result:
        :return:
        """
        # endpoint /v1/sessions/{sessions_id}/action
        endpoint = '{0}{1}/action'.format(self.endpoint, session_id)
        doc = {"end": {
            "job_id": job_id,
            "current_tag": session_tag,
            "result": result
            }}
        r = requests.post(endpoint,
                          headers=self.headers,
                          data=json.dumps(doc),
                          verify=self.verify)
        if r.status_code != 202:
            raise exceptions.ApiClientException(r)
        return r.json()
