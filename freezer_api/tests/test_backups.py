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

import falcon
from freezer_api.api.v1 import backups
from freezer_api.common.exceptions import *

from common import *


class TestBackupsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = {'X-User-ID': fake_data_0_user_id}
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = backups.BackupsCollectionResource(self.mock_db)

    def test_on_get_return_empty_list(self):
        self.mock_db.get_backup.return_value = []
        expected_result = {'backups': []}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_get_return_correct_list(self):
        self.mock_db.get_backup.return_value = [fake_data_0_backup_metadata]
        expected_result = {'backups': [fake_data_0_backup_metadata]}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_body(self):
        self.mock_db.add_backup.return_value = [fake_data_0_wrapped_backup_metadata['backup_id']]
        expected_result = {'backup_id': fake_data_0_wrapped_backup_metadata['backup_id']}
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    def test_on_post_inserts_correct_data(self):
        self.mock_req.context['doc'] = fake_data_0_backup_metadata
        self.mock_db.add_backup.return_value = fake_data_0_wrapped_backup_metadata['backup_id']
        self.resource.on_post(self.mock_req, self.mock_req)
        expected_result = {'backup_id': fake_data_0_wrapped_backup_metadata['backup_id']}
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)


class TestBackupsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = {'X-User-ID': fake_data_0_user_id}
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = backups.BackupsResource(self.mock_db)

    def test_on_get_return_no_result_and_404_when_not_found(self):
        self.mock_db.get_backup.return_value = []
        self.resource.on_get(self.mock_req, self.mock_req, fake_data_0_wrapped_backup_metadata['backup_id'])
        self.assertNotIn('result', self.mock_req.context)
        self.assertEqual(self.mock_req.status, falcon.HTTP_404)

    def test_on_get_return_correct_data(self):
        self.mock_db.get_backup.return_value = [fake_data_0_wrapped_backup_metadata]
        expected_result = [fake_data_0_wrapped_backup_metadata]
        self.resource.on_get(self.mock_req, self.mock_req, fake_data_0_wrapped_backup_metadata['backup_id'])
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_delete_removes_proper_data(self):
        #self.mock_db.delete_backup.return_value = True
        self.resource.on_delete(self.mock_req, self.mock_req, fake_data_0_backup_id)
        result = self.mock_req.context['result']
        expected_result = {'backup_id': fake_data_0_backup_id}
        self.assertEquals(self.mock_req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)
