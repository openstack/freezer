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
import unittest
from mock import Mock, patch

from freezer.apiclient import exceptions
from freezer.apiclient import sessions


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock()
        self.mock_response = Mock()
        self.mock_client.endpoint = 'http://testendpoint:9999'
        self.mock_client.auth_token = 'testtoken'
        self.mock_client.client_id = 'test_client_id_78900987'
        self.session_manager = sessions.SessionManager(self.mock_client)
        self.endpoint = 'http://testendpoint:9999/v1/sessions/'
        self.headers = {'X-Auth-Token': 'testtoken'}

    @patch('freezer.apiclient.sessions.requests')
    def test_create(self, mock_requests):
        self.assertEqual(self.endpoint, self.session_manager.endpoint)
        self.assertEqual(self.headers, self.session_manager.headers)

    @patch('freezer.apiclient.sessions.requests')
    def test_create_ok(self, mock_requests):
        self.mock_response.status_code = 201
        self.mock_response.json.return_value = {'session_id': 'qwerqwer'}
        mock_requests.post.return_value = self.mock_response
        retval = self.session_manager.create({'session': 'metadata'})
        self.assertEqual('qwerqwer', retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_create_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        self.mock_response.status_code = 500
        mock_requests.post.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.create, {'session': 'metadata'})

    @patch('freezer.apiclient.sessions.requests')
    def test_delete_ok(self, mock_requests):
        self.mock_response.status_code = 204
        mock_requests.delete.return_value = self.mock_response
        retval = self.session_manager.delete('test_session_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_delete_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        self.mock_response.status_code = 500
        mock_requests.delete.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.delete, 'test_session_id')

    @patch('freezer.apiclient.sessions.requests')
    def test_get_ok(self, mock_requests):
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {'session_id': 'qwerqwer'}
        mock_requests.get.return_value = self.mock_response
        retval = self.session_manager.get('test_session_id')
        self.assertEqual({'session_id': 'qwerqwer'}, retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_get_raise_ApiClientException_when_api_return_error_different_from_404(self, mock_requests):
        self.mock_response.status_code = 500
        mock_requests.get.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.get, 'test_session_id')

    @patch('freezer.apiclient.sessions.requests')
    def test_get_none(self, mock_requests):
        self.mock_response.status_code = 404
        mock_requests.get.return_value = self.mock_response
        retval = self.session_manager.get('test_session_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_list_ok(self, mock_requests):
        self.mock_response.status_code = 200
        session_list = [{'session_id_0': 'bomboloid'}, {'session_id_1': 'asdfasdf'}]
        self.mock_response.json.return_value = {'sessions': session_list}
        mock_requests.get.return_value = self.mock_response
        retval = self.session_manager.list()
        self.assertEqual(session_list, retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_list_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        self.mock_response.status_code = 404
        session_list = [{'session_id_0': 'bomboloid'}, {'session_id_1': 'asdfasdf'}]
        self.mock_response.json.return_value = {'clients': session_list}
        mock_requests.get.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.list)

    @patch('freezer.apiclient.sessions.requests')
    def test_update_ok(self, mock_requests):
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            "patch": {"status": "bamboozled"},
            "version": 12,
            "session_id": "d454beec-1f3c-4d11-aa1a-404116a40502"
        }
        mock_requests.patch.return_value = self.mock_response
        retval = self.session_manager.update('d454beec-1f3c-4d11-aa1a-404116a40502', {'status': 'bamboozled'})
        self.assertEqual(12, retval)

    @patch('freezer.apiclient.sessions.requests')
    def test_update_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        self.mock_response.json.return_value = {
            "patch": {"status": "bamboozled"},
            "version": 12,
            "session_id": "d454beec-1f3c-4d11-aa1a-404116a40502"
        }
        self.mock_response.status_code = 404
        self.mock_response.text = '{"title": "Not Found","description":"No document found with ID d454beec-1f3c-4d11-aa1a-404116a40502x"}'
        mock_requests.patch.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.update,
                          'd454beec-1f3c-4d11-aa1a-404116a40502', {'status': 'bamboozled'})

    @patch('freezer.apiclient.sessions.requests')
    def test_add_job_uses_proper_endpoint(self, mock_requests):
        session_id, job_id = 'sessionqwerty1234', 'jobqwerty1234'
        self.mock_response.status_code = 204
        mock_requests.put.return_value = self.mock_response
        endpoint = '{0}{1}/jobs/{2}'.format(self.endpoint, session_id, job_id)

        retval = self.session_manager.add_job(session_id, job_id)

        self.assertIsNone(retval)
        mock_requests.put.assert_called_with(endpoint, headers=self.headers, verify=True)

    @patch('freezer.apiclient.sessions.requests')
    def test_add_job_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        session_id, job_id = 'sessionqwerty1234', 'jobqwerty1234'
        self.mock_response.status_code = 500
        mock_requests.put.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.add_job, session_id, job_id)

    @patch('freezer.apiclient.sessions.requests')
    def test_remove_job_uses_proper_endpoint(self, mock_requests):
        session_id, job_id = 'sessionqwerty1234', 'jobqwerty1234'
        self.mock_response.status_code = 204
        mock_requests.delete.return_value = self.mock_response
        endpoint = '{0}{1}/jobs/{2}'.format(self.endpoint, session_id, job_id)

        retval = self.session_manager.remove_job(session_id, job_id)

        self.assertIsNone(retval)
        mock_requests.delete.assert_called_with(endpoint, headers=self.headers, verify=True)

    @patch('freezer.apiclient.sessions.requests')
    def test_remove_job_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        session_id, job_id = 'sessionqwerty1234', 'jobqwerty1234'
        self.mock_response.status_code = 500
        mock_requests.delete.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.remove_job, session_id, job_id)

    @patch('freezer.apiclient.sessions.requests')
    def test_start_session_posts_proper_data(self, mock_requests):
        session_id, job_id, tag = 'sessionqwerty1234', 'jobqwerty1234', 23
        self.mock_response.status_code = 202
        self.mock_response.json.return_value = {'result': 'success', 'session_tag': 24}
        mock_requests.post.return_value = self.mock_response
        # /v1/sessions/{sessions_id}/action
        endpoint = '{0}{1}/action'.format(self.endpoint, session_id)
        data = {"start": {"current_tag": 23, "job_id": "jobqwerty1234"}}
        retval = self.session_manager.start_session(session_id, job_id, tag)
        self.assertEqual({'result': 'success', 'session_tag': 24}, retval)

        args = mock_requests.post.call_args[0]
        kwargs = mock_requests.post.call_args[1]
        self.assertEquals(endpoint, args[0])
        self.assertEquals(data, json.loads(kwargs['data']))
        self.assertEquals(self.headers, kwargs['headers'])

    @patch('freezer.apiclient.sessions.requests')
    def test_start_session_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        session_id, job_id, tag = 'sessionqwerty1234', 'jobqwerty1234', 23
        self.mock_response.status_code = 500
        self.mock_response.json.return_value = {'result': 'success', 'session_tag': 24}
        mock_requests.post.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.start_session,
                          session_id, job_id, tag)

    @patch('freezer.apiclient.sessions.requests')
    def test_end_session_posts_proper_data(self, mock_requests):
        session_id, job_id, tag = 'sessionqwerty1234', 'jobqwerty1234', 23
        self.mock_response.status_code = 202
        self.mock_response.json.return_value = {'result': 'success', 'session_tag': 24}
        mock_requests.post.return_value = self.mock_response
        # /v1/sessions/{sessions_id}/action
        endpoint = '{0}{1}/action'.format(self.endpoint, session_id)
        data = {"end": {"current_tag": 23, "job_id": "jobqwerty1234", "result": "fail"}}
        retval = self.session_manager.end_session(session_id, job_id, tag, 'fail')
        self.assertEqual({'result': 'success', 'session_tag': 24}, retval)

        args = mock_requests.post.call_args[0]
        kwargs = mock_requests.post.call_args[1]
        self.assertEquals(endpoint, args[0])
        self.assertEquals(data, json.loads(kwargs['data']))
        self.assertEquals(self.headers, kwargs['headers'])

    @patch('freezer.apiclient.sessions.requests')
    def test_end_session_raise_ApiClientException_when_api_return_error_code(self, mock_requests):
        session_id, job_id, tag = 'sessionqwerty1234', 'jobqwerty1234', 23
        self.mock_response.status_code = 500
        self.mock_response.json.return_value = {'result': 'success', 'session_tag': 24}
        mock_requests.post.return_value = self.mock_response
        self.assertRaises(exceptions.ApiClientException, self.session_manager.end_session,
                          session_id, job_id, tag, 'fail')
