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
from freezer.apiclient import backups


class CallArgs(object):

    def __init__(self, mock_obj=Mock()):
        self.args = mock_obj.call_args[0]
        self.kwargs = mock_obj.call_args[1]

    def _check_arg(self, arg, value, load_json):
        if load_json:
            arg = json.loads(arg)
        if (arg != value):
            raise Exception("Argument doesn't match: {0} != {1}".format(arg, value))
        return

    def check_arg(self, pos, value, load_json=False):
        if isinstance(pos, int):
            return self._check_arg(self.args[pos], value, load_json)
        return self._check_arg(self.kwargs[pos], value, load_json)


class TestBackupManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock()
        self.mock_client.client_id = "jumpingjack"
        self.mock_client.endpoint = 'http://testendpoint:9999'
        self.mock_client.auth_token = 'testtoken'
        self.b = backups.BackupsManager(self.mock_client)

    @patch('freezer.apiclient.backups.requests')
    def test_create(self, mock_requests):
        self.assertEqual('http://testendpoint:9999/v1/backups/', self.b.endpoint)
        self.assertEqual({'X-Auth-Token': 'testtoken'}, self.b.headers)

    @patch('freezer.apiclient.backups.requests')
    def test_create_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.post.return_value = mock_response
        retval = self.b.create(backup_metadata={'backup': 'metadata'})
        ca = CallArgs(mock_requests.post)
        ca.check_arg(0, 'http://testendpoint:9999/v1/backups/')
        ca.check_arg('data', {"backup": "metadata", "client_id": "jumpingjack"}, load_json=True)
        ca.check_arg('headers', {'X-Auth-Token': 'testtoken'})
        ca.check_arg('verify', True)
        self.assertEqual('qwerqwer', retval)

    @patch('freezer.apiclient.backups.requests')
    def test_create_ok_with_client_id(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.post.return_value = mock_response
        retval = self.b.create(backup_metadata={'backup': 'metadata', 'client_id': 'wahwah'})
        ca = CallArgs(mock_requests.post)
        ca.check_arg(0, 'http://testendpoint:9999/v1/backups/')
        ca.check_arg('data', {"backup": "metadata", "client_id": "wahwah"}, load_json=True)
        ca.check_arg('headers', {'X-Auth-Token': 'testtoken'})
        ca.check_arg('verify', True)
        self.assertEqual('qwerqwer', retval)

    @patch('freezer.apiclient.backups.requests')
    def test_create_fail_when_api_return_error_code(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.b.create, {'backup': 'metadata'})

    @patch('freezer.apiclient.backups.requests')
    def test_delete_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response
        retval = self.b.delete('test_backup_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.backups.requests')
    def test_delete_fail(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.delete.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.b.delete, 'test_backup_id')

    @patch('freezer.apiclient.backups.requests')
    def test_get_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.get.return_value = mock_response
        retval = self.b.get('test_backup_id')
        self.assertEqual({'backup_id': 'qwerqwer'}, retval)

    @patch('freezer.apiclient.backups.requests')
    def test_get_none(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response
        retval = self.b.get('test_backup_id')
        self.assertIsNone(retval)

    @patch('freezer.apiclient.backups.requests')
    def test_get_error(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_requests.get.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException,
                          self.b.get, 'test_backup_id')

    @patch('freezer.apiclient.backups.requests')
    def test_list_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        backup_list = [{'backup_id_0': 'qwerqwer'}, {'backup_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'backups': backup_list}
        mock_requests.get.return_value = mock_response
        retval = self.b.list()
        self.assertEqual(backup_list, retval)


    @patch('freezer.apiclient.backups.requests')
    def test_list_parameters(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        backup_list = [{'backup_id_0': 'qwerqwer'}, {'backup_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'backups': backup_list}
        mock_requests.get.return_value = mock_response
        retval = self.b.list(limit=5,
                             offset=5,
                             search={"time_before": 1428529956})
        ca = CallArgs(mock_requests.get)
        ca.check_arg(0, 'http://testendpoint:9999/v1/backups/')
        ca.check_arg('data', {"time_before": 1428529956, "match": [{"client_id": "jumpingjack"}]}, load_json=True)
        ca.check_arg('headers', {'X-Auth-Token': 'testtoken'})
        ca.check_arg('verify', True)
        self.assertEqual(backup_list, retval)

    @patch('freezer.apiclient.backups.requests')
    def test_list_error(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        backup_list = [{'backup_id_0': 'qwerqwer'}, {'backup_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'backups': backup_list}
        mock_requests.get.return_value = mock_response
        self.assertRaises(exceptions.ApiClientException, self.b.list)
