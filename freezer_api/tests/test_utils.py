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
from freezer_api.common import utils


DATA_backup_metadata = {
    "container": "freezer_container",
    "host_name": "alpha",
    "backup_name": "important_data_backup",
    "timestamp": 12341234,
    "level": 0,
    "backup_session": 12341234,
    "max_level": 5,
    "mode" : "fs",
    "fs_real_path": "/blabla",
    "vol_snap_path": "/blablasnap",
    "total_broken_links" : 0,
    "total_fs_files": 11,
    "total_directories": 2,
    "backup_size_uncompressed": 12112342,
    "backup_size_compressed": 1214322,
    "total_backup_session_size": 1212,
    "compression_alg": "None",
    "encrypted": "false",
    "client_os": "linux",
    "broken_links": ["link_01", "link_02"],
    "excluded_files": ["excluded_file_01", "excluded_file_02"],
    'cli': 'whatever'
}

DATA_user_id = 'AUx6F07NwlhuOVELWtHx'

DATA_user_name = 'gegrex55NPlwlhuOVELWtHv'

DATA_backup_id = 'freezer_container_alpha_important_data_backup_12341234_0'

DATA_wrapped_backup_metadata = {
    'user_id': DATA_user_id,
    'user_name': DATA_user_name,
    'backup_id': DATA_backup_id,
    'backup_medatada': {
        "container": "freezer_container",
        "host_name": "alpha",
        "backup_name": "important_data_backup",
        "timestamp": 12341234,
        "level": 0,
        "backup_session": 12341234,
        "max_level": 5,
        "mode": "fs",
        "fs_real_path": "/blabla",
        "vol_snap_path": "/blablasnap",
        "total_broken_links" : 0,
        "total_fs_files": 11,
        "total_directories": 2,
        "backup_size_uncompressed": 12112342,
        "backup_size_compressed": 1214322,
        "total_backup_session_size": 1212,
        "compression_alg": "None",
        "encrypted": "false",
        "client_os": "linux",
        "broken_links": ["link_01", "link_02"],
        "excluded_files": ["excluded_file_01", "excluded_file_02"],
        'cli': 'whatever'
    }
}


class TestBackupMetadataDoc(unittest.TestCase):

    def setUp(self):
        self.backup_metadata = utils.BackupMetadataDoc(
            user_id=DATA_user_id,
            user_name=DATA_user_name,
            data=DATA_backup_metadata)

    def test_backup_id(self):
        assert (self.backup_metadata.backup_id == DATA_backup_id)

    def test_is_valid_return_True_when_valid(self):
        self.assertTrue(self.backup_metadata.is_valid())

    def test_is_valid_returns_False_when_user_id_empty(self):
        self.backup_metadata.user_id = ''
        self.assertFalse(self.backup_metadata.is_valid())

    def test_backup_id_correct(self):
        self.assertEqual(self.backup_metadata.backup_id, DATA_backup_id)
        self.backup_metadata.data['container'] = 'different'
        self.assertNotEqual(self.backup_metadata.backup_id, DATA_backup_id)
