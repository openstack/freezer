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

import falcon
from freezer_api.api.v1 import backups
from freezer_api.storage import simpledict

from common import *
from freezer_api.common.exceptions import *


class TestBackupsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.db = simpledict.SimpleDictStorageEngine()
        self.resource = backups.BackupsCollectionResource(self.db)
        self.req = FakeReqResp()
        self.req.header['X-User-ID'] = fake_data_0_user_id

    def test_on_get_return_empty_list(self):
        expected_result = {'backups': []}
        self.resource.on_get(self.req, self.req)
        result = self.req.context['result']
        self.assertEqual(result, expected_result)

    def test_on_get_return_correct_list(self):
        self.db.add_backup(user_id=fake_data_0_user_id,
                           user_name=fake_data_0_user_name,
                           data=fake_data_0_backup_metadata)
        self.resource.on_get(self.req, self.req)
        result = self.req.context['result']
        expected_result = {'backups': [fake_data_0_wrapped_backup_metadata]}
        self.assertEqual(result, expected_result)

    def test_on_get_return_empty_list_without_user_id(self):
        self.req.header.pop('X-User-ID')
        self.db.add_backup(user_id=fake_data_0_user_id,
                           user_name=fake_data_0_user_name,
                           data=fake_data_0_backup_metadata)
        self.resource.on_get(self.req, self.req)
        result = self.req.context['result']
        expected_result = {'backups': []}
        self.assertEqual(result, expected_result)

    def test_on_get_return_empty_list_with_different_user_id(self):
        self.req.header['X-User-ID'] = 'LupinIII'
        self.db.add_backup(user_id=fake_data_0_user_id,
                           user_name=fake_data_0_user_name,
                           data=fake_data_0_backup_metadata)
        self.resource.on_get(self.req, self.req)
        result = self.req.context['result']
        expected_result = {'backups': []}
        self.assertEqual(result, expected_result)

    def test_on_post_raises_when_missing_body(self):
        self.assertRaises(BadDataFormat, self.resource.on_post, self.req, self.req)

    def test_on_post_inserts_correct_data(self):
        self.req.context['doc'] = fake_data_0_backup_metadata
        self.resource.on_post(self.req, self.req)
        self.assertEquals(self.req.status, falcon.HTTP_201)
        expected_result = {'backup_id': fake_data_0_backup_id}
        self.assertEquals(self.req.context['result'], expected_result)


class TestBackupsResource(unittest.TestCase):

    def setUp(self):
        self.db = simpledict.SimpleDictStorageEngine()
        self.resource = backups.BackupsResource(self.db)
        self.req = FakeReqResp()
        self.req.header['X-User-ID'] = fake_data_0_user_id

    def test_on_get_raises_when_not_found(self):
        self.assertRaises(ObjectNotFound, self.resource.on_get, self.req, self.req, fake_data_0_backup_id)

    def test_on_get_return_correct_data(self):
        self.db.add_backup(user_id=fake_data_0_user_id,
                           user_name=fake_data_0_user_name,
                           data=fake_data_0_backup_metadata)
        self.resource.on_get(self.req, self.req, fake_data_0_backup_id)
        result = self.req.context['result']
        self.assertEqual(result, fake_data_0_wrapped_backup_metadata)

    def test_on_delete_raises_when_not_found(self):
        self.assertRaises(ObjectNotFound, self.resource.on_delete, self.req, self.req, fake_data_0_backup_id)

    def test_on_delete_removes_proper_data(self):
        self.db.add_backup(user_id=fake_data_0_user_id,
                           user_name=fake_data_0_user_name,
                           data=fake_data_0_backup_metadata)
        self.resource.on_delete(self.req, self.req, fake_data_0_backup_id)
        result = self.req.context['result']
        expected_result = {'backup_id': fake_data_0_backup_id}
        self.assertEquals(self.req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)
