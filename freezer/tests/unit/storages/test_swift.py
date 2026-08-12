# (c) Copyright 2026 Alvaro Soto <alsotoes@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
from unittest import mock

from freezer.storage import swift


class TestSwiftStorageListdir(unittest.TestCase):

    def setUp(self):
        self.client_manager = mock.Mock()
        self.swift_conn = mock.Mock()
        self.client_manager.create_swift.return_value = self.swift_conn
        self.storage = swift.SwiftStorage(
            self.client_manager, 'mycontainer', 1024, skip_prepare=True)

    def test_listdir_returns_subdir_names(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'subdir': 'mycontainer/metadata/engine/host/1467649589/'},
             {'subdir': 'mycontainer/metadata/engine/host/1467649588/'}]
        )
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, {'1467649589', '1467649588'})

    def test_listdir_returns_file_names(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'name': 'mycontainer/metadata/engine/host/1467649589'},
             {'name': 'mycontainer/metadata/engine/host/1467649588'}]
        )
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, {'1467649589', '1467649588'})

    def test_listdir_returns_mixed_entries(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'subdir': 'mycontainer/metadata/engine/host/1467649589/'},
             {'name': 'mycontainer/metadata/engine/host/stray_file'}]
        )
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, {'1467649589', 'stray_file'})

    def test_listdir_returns_empty_set_for_no_entries(self):
        self.swift_conn.get_container.return_value = (None, [])
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, set())

    def test_listdir_returns_empty_set_on_exception(self):
        self.swift_conn.get_container.side_effect = Exception('fail')
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, set())

    def test_listdir_uses_full_listing_and_delimiter(self):
        self.swift_conn.get_container.return_value = (None, [])
        self.storage.listdir('mycontainer/metadata/engine/host')
        self.swift_conn.get_container.assert_called_once_with(
            container='mycontainer',
            full_listing=True,
            prefix='metadata/engine/host/',
            delimiter='/')

    def test_listdir_ignores_entries_without_name_or_subdir(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'subdir': 'mycontainer/metadata/engine/host/ts1/'},
             {'name': 'mycontainer/metadata/engine/host/ts2'},
             {}]
        )
        result = self.storage.listdir(
            'mycontainer/metadata/engine/host')
        self.assertEqual(result, {'ts1', 'ts2'})


class TestSwiftStorageRmtree(unittest.TestCase):

    def setUp(self):
        self.client_manager = mock.Mock()
        self.swift_conn = mock.Mock()
        self.client_manager.create_swift.return_value = self.swift_conn
        self.storage = swift.SwiftStorage(
            self.client_manager, 'mycontainer', 1024, skip_prepare=True)

    def test_rmtree_deletes_all_objects_under_prefix(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'name': 'data/engine/host/1467649589/0_1467649589/data'},
             {'name': ('data/engine/host/1467649589/0_1467649589/'
                       'engine_metadata')},
             {'name': ('data/engine/host/1467649589/0_1467649589/'
                       'segments/00000000')},
             {'name': ('data/engine/host/1467649589/0_1467649589/'
                       'segments/00000001')}]
        )
        self.storage.rmtree(
            'mycontainer/data/engine/host/1467649589')
        assert self.swift_conn.delete_object.call_count == 4
        self.swift_conn.delete_object.assert_any_call(
            'mycontainer',
            'data/engine/host/1467649589/0_1467649589/data')
        self.swift_conn.delete_object.assert_any_call(
            'mycontainer',
            'data/engine/host/1467649589/0_1467649589/engine_metadata')
        self.swift_conn.delete_object.assert_any_call(
            'mycontainer',
            'data/engine/host/1467649589/0_1467649589/segments/00000000')

    def test_rmtree_uses_full_listing(self):
        self.swift_conn.get_container.return_value = (None, [])
        self.storage.rmtree(
            'mycontainer/data/engine/host/1467649589')
        self.swift_conn.get_container.assert_called_once_with(
            'mycontainer',
            prefix='data/engine/host/1467649589',
            full_listing=True)

    def test_rmtree_raises_on_delete_error(self):
        self.swift_conn.get_container.return_value = (
            None,
            [{'name': 'data/engine/host/1467649589/0_1467649589/data'}]
        )
        self.swift_conn.delete_object.side_effect = Exception('delete failed')
        with self.assertRaises(Exception) as cm:  # noqa
            self.storage.rmtree(
                'mycontainer/data/engine/host/1467649589')
        self.assertIn('delete failed', str(cm.exception))

    def test_rmtree_handles_empty_listing(self):
        self.swift_conn.get_container.return_value = (None, [])
        self.storage.rmtree(
            'mycontainer/data/engine/host/1467649589')
        self.swift_conn.delete_object.assert_not_called()
