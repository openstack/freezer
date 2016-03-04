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

import unittest
from mock import Mock, patch

from freezer.apiclient import exceptions
from freezer.apiclient import registration


class TestRegistrationManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock()
        self.mock_client.endpoint = 'http://testendpoint:9999'
        self.mock_client.auth_token = 'testtoken'
        self.r = registration.RegistrationManager(self.mock_client)

    @patch('freezer.apiclient.registration.requests')
    def test_create(self, mock_requests):
        self.assertEqual('http://testendpoint:9999/v1/clients/', self.r.endpoint)
        self.assertEqual({'X-Auth-Token': 'testtoken'}, self.r.headers)

    @patch('freezer.apiclient.registration.requests')
    def test_create_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'client_id': 'qwerqwer'}
        mock_requests.post.return_value = mock_response
        retval = self.r.create(client_info={'client': 'metadata'})
        self.assertEqual('qwerqwer', retval)

    @patch('freezer.apiclient.registration.requests')
    def test_create_fail_when_api_return_error_code(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.r.create, {'client': 'metadata'})

    @patch('freezer.apiclient.registration.requests')
    def test_delete_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response
        retval = self.r.delete('test_client_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.registration.requests')
    def test_delete_fail(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.delete.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.r.delete, 'test_client_id')

    @patch('freezer.apiclient.registration.requests')
    def test_get_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'client_id': 'qwerqwer'}
        mock_requests.get.return_value = mock_response
        retval = self.r.get('test_client_id')
        self.assertEqual({'client_id': 'qwerqwer'}, retval)

    @patch('freezer.apiclient.registration.requests')
    def test_get_none(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response
        retval = self.r.get('test_client_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.registration.requests')
    def test_get_raises_ApiClientException_on_error_not_404(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.r.get, 'test_client_id')

    @patch('freezer.apiclient.registration.requests')
    def test_list_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        client_list = [{'client_id_0': 'qwerqwer'}, {'client_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'clients': client_list}
        mock_requests.get.return_value = mock_response
        retval = self.r.list()
        self.assertEqual(client_list, retval)

    @patch('freezer.apiclient.registration.requests')
    def test_list_error(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        client_list = [{'client_id_0': 'qwerqwer'}, {'client_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'clients': client_list}
        mock_requests.get.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.r.list)

