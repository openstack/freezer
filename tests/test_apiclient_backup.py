"""Freezer swift.py related tests

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

import unittest
from mock import Mock, patch

from freezer.apiclient import exceptions
from freezer.apiclient import backups


class TestBackupManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock()
        self.mock_client.api_endpoint = 'http://testendpoint:9999'
        self.mock_client.auth_token = 'testtoken'
        self.b = backups.BackupsManager(self.mock_client)

    @patch('freezer.apiclient.backups.requests')
    def test_create(self, mock_requests):
        self.assertEqual(self.b.endpoint, 'http://testendpoint:9999/v1/backups/')
        self.assertEqual(self.b.headers, {'X-Auth-Token': 'testtoken'})

    @patch('freezer.apiclient.backups.requests')
    def test_create_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.post.return_value = mock_response
        retval = self.b.create(backup_metadata={'backup': 'metadata'})
        self.assertEqual(retval, 'qwerqwer')

    @patch('freezer.apiclient.backups.requests')
    def test_create_fail(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        #mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.post.return_value = mock_response
        self.assertRaises(exceptions.MetadataCreationFailure, self.b.create, {'backup': 'metadata'})

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
        self.assertRaises(exceptions.MetadataDeleteFailure, self.b.delete, 'test_backup_id')

    @patch('freezer.apiclient.backups.requests')
    def test_get_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'backup_id': 'qwerqwer'}
        mock_requests.get.return_value = mock_response
        retval = self.b.get('test_backup_id')
        self.assertEqual(retval, {'backup_id': 'qwerqwer'})

    @patch('freezer.apiclient.backups.requests')
    def test_get_none(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response
        retval = self.b.get('test_backup_id')
        self.assertIsNone(retval)

    # get_error

    @patch('freezer.apiclient.backups.requests')
    def test_list_ok(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        backup_list = [{'backup_id_0': 'qwerqwer'}, {'backup_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'backups': backup_list}
        mock_requests.get.return_value = mock_response
        retval = self.b.list()
        self.assertEqual(retval, backup_list)

    @patch('freezer.apiclient.backups.requests')
    def test_list_error(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        backup_list = [{'backup_id_0': 'qwerqwer'}, {'backup_id_1': 'asdfasdf'}]
        mock_response.json.return_value = {'backups': backup_list}
        mock_requests.get.return_value = mock_response
        self.assertRaises(exceptions.MetadataGetFailure, self.b.list)
