"""Freezer backup.py related tests

(c) Copyright 2018 ZTE Corporation.
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

from unittest import mock

from freezer.openstack import backup
from freezer.tests import commons
from freezer.utils import utils


class TestBackup(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestBackup, self).setUp()
        self.backup_opt = commons.BackupOpt1()
        self.bakup_os = backup.BackupOs(self.backup_opt.client_manager,
                                        self.backup_opt.container,
                                        self.backup_opt.storage,
                                        self.backup_opt.temp_resource_prefix)

    def test_backup_cinder_by_glance(self):
        self.bakup_os.backup_cinder_by_glance(35)

    def test_backup_cinder_by_glance_none_name(self):
        self.bakup_os.backup_cinder_by_glance(10230)

    def test_backup_cinder_with_incremental(self):
        cinder = self.bakup_os.client_manager.get_cinder()
        with mock.patch.object(
            cinder, 'backups',
            return_value=[commons.FakeIdObject(4)]
        ) as mock_backups, \
                mock.patch.object(
                    cinder, 'create_backup') as mock_create_backup:
            self.bakup_os.backup_cinder(35, incremental=True)
            mock_backups.assert_called_once_with(
                details=False, volume_id=35, status='available')
            mock_create_backup.assert_called_once_with(
                volume_id=35,
                container=self.bakup_os.container,
                name=None,
                description=None,
                is_incremental=True,
                force=True
            )

    def test_backup_cinder_without_incremental(self):
        cinder = self.bakup_os.client_manager.get_cinder()
        with mock.patch.object(cinder, 'create_backup') as mock_create_backup:
            self.bakup_os.backup_cinder(35, incremental=False)
            mock_create_backup.assert_called_once_with(
                volume_id=35,
                container=self.bakup_os.container,
                name=None,
                description=None,
                is_incremental=False,
                force=True
            )

    def test_backup_cinder_with_none(self):
        cinder = self.bakup_os.client_manager.get_cinder()
        with mock.patch.object(
            cinder, 'backups', return_value=[]
        ) as mock_backups, \
                mock.patch.object(
                    cinder, 'create_backup') as mock_create_backup:
            self.bakup_os.backup_cinder(10240, incremental=True)
            mock_backups.assert_called_once_with(
                details=False, volume_id=10240, status='available')
            mock_create_backup.assert_called_once_with(
                volume_id=10240,
                container=self.bakup_os.container,
                name=None,
                description=None,
                is_incremental=False,
                force=True
            )

    def test_backup_cinder_by_snapshot_timestamp(self):
        volume_id = 12345
        # Mock the snapshot object to have a specific created_at
        mock_snapshot = commons.FakeIdObject("snapshot_id")
        # 1463018422 is 2016-05-12 02:00:22 UTC
        mock_snapshot.created_at = '2016-05-12T02:00:22.123456'

        self.backup_opt.client_manager.provide_snapshot = \
            mock.Mock(return_value=mock_snapshot)
        self.bakup_os.storage.add_stream = mock.Mock()

        self.bakup_os.backup_cinder_by_glance(volume_id)

        expected_dt = '2016-05-12T02:00:22'
        expected_timestamp = utils.DateTime(expected_dt).timestamp
        expected_package = "{0}/{1}".format(volume_id, expected_timestamp)

        # Verify storage.add_stream was called with the correct package name
        self.bakup_os.storage.add_stream.assert_called()
        args, _ = self.bakup_os.storage.add_stream.call_args
        # add_stream(self, stream, package_name, headers=None)
        # In backup.py: storage.add_stream(stream, package, headers=headers)
        self.assertEqual(args[1], expected_package)

        cinder = self.bakup_os.client_manager.get_cinder()
        with mock.patch.object(cinder, 'create_backup') as mock_create_backup:
            self.bakup_os.backup_cinder(
                35, incremental=False, availability_zone='my_az')
            mock_create_backup.assert_called_once_with(
                volume_id=35,
                container=self.bakup_os.container,
                name=None,
                description=None,
                is_incremental=False,
                force=True,
                availability_zone='my_az'
            )

    def test_backup_cinder_with_custom_container(self):
        bakup_os = backup.BackupOs(self.backup_opt.client_manager,
                                   'my_custom_container',
                                   self.backup_opt.storage,
                                   self.backup_opt.temp_resource_prefix)
        cinder = bakup_os.client_manager.get_cinder()
        with mock.patch.object(cinder, 'create_backup') as mock_create_backup:
            bakup_os.backup_cinder(35, incremental=False)
            mock_create_backup.assert_called_once_with(
                volume_id=35,
                container='my_custom_container',
                name=None,
                description=None,
                is_incremental=False,
                force=True
            )
