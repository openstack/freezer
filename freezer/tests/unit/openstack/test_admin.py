"""Freezer admin.py related tests

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

from freezer.openstack import admin
from freezer.tests import commons


class TestAdmin(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestAdmin, self).setUp()
        self.backup_opt = commons.BackupOpt1()
        self.admin_os = admin.AdminOs(self.backup_opt.client_manager)
        self.client_manager = self.backup_opt.client_manager

    def test_del_cinderbackup_and_dependend_incremental(self):
        self.admin_os.del_cinderbackup_and_dependend_incremental(1)
        try:
            self.admin_os.del_cinderbackup_and_dependend_incremental(1023)
        except Exception as e:
            msg = "Delete backup 1023 failed, the status of backup is error."
            self.assertEqual(msg, str(e))

        try:
            self.admin_os.del_cinderbackup_and_dependend_incremental(1024)
        except Exception as e:
            msg = "Delete backup 1024 failed due to timeout over 120s," \
                  " the status of backup is deleting."
            self.assertEqual(msg, str(e))

    def test_del_off_limit_fullbackup_keep(self):
        self.admin_os.del_off_limit_fullbackup('2', 1)

    def test_del_off_limit_fullbackup_keep_two(self):
        self.admin_os.del_off_limit_fullbackup('2', 2)

    def test_del_off_limit_fullbackup_freezer_only_ignores_user_backups(self):
        user_backup = commons.FakeIdObject(100)
        user_backup.metadata = {}
        freezer_backup_1 = commons.FakeIdObject(101)
        freezer_backup_1.metadata = {'created_by': 'freezer'}
        freezer_backup_2 = commons.FakeIdObject(102)
        freezer_backup_2.metadata = {'created_by': 'freezer'}

        backups = [user_backup, freezer_backup_1, freezer_backup_2]

        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=backups))
        self.admin_os.del_cinderbackup_and_dependend_incremental = (
            commons.mock.Mock(return_value=[101]))

        # Keep 1 full backup; out of 2 freezer backups, 1 should be deleted
        # (101). User backup (100) should be ignored.
        self.admin_os.del_off_limit_fullbackup('vol1', 1, freezer_only=True)
        (self.admin_os.del_cinderbackup_and_dependend_incremental
            .assert_called_once_with(101))

    def test_remove_cinderbackup_older_than(self):
        self.admin_os.remove_cinderbackup_older_than(35, 1463896546.0)
        try:
            self.admin_os.remove_cinderbackup_older_than(1023, 1463896546.0)
        except Exception as e:
            msg = "Delete backup 1023 failed, the status of backup is error."
            self.assertEqual(msg, str(e))

        try:
            self.admin_os.remove_cinderbackup_older_than(1024, 1463896546.0)
        except Exception as e:
            msg = "Delete backup 1024 failed due to timeout over 120s," \
                  " the status of backup is deleting."
            self.assertEqual(msg, str(e))

    def test_delete_single_backup_returns_freezer_backup_id(self):
        cinder_backup = commons.FakeIdObject('cinder_101')
        cinder_backup.metadata = {'created_by': 'freezer',
                                  'freezer_backup_id': 'freezer_uuid_999'}
        self.admin_os.cinder_client.get_backup = commons.mock.Mock(
            return_value=cinder_backup)
        self.admin_os.cinder_client.delete_backup = commons.mock.Mock()
        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=[]))

        fid = self.admin_os._delete_single_backup('cinder_101')

        self.admin_os.cinder_client.delete_backup.assert_called_once_with(
            'cinder_101')
        self.assertEqual('freezer_uuid_999', fid)

    def test_delete_single_backup_get_backup_fails(self):
        self.admin_os.cinder_client.get_backup = commons.mock.Mock(
            side_effect=Exception("API connection error"))
        self.admin_os.cinder_client.delete_backup = commons.mock.Mock()
        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=[]))

        fid = self.admin_os._delete_single_backup('cinder_101')

        self.admin_os.cinder_client.delete_backup.assert_called_once_with(
            'cinder_101')
        self.assertIsNone(fid)

    def test_is_freezer_backup_and_get_freezer_backup_id(self):
        # Backup created with freezer-api (has both tags)
        valid_b1 = commons.FakeIdObject('1')
        valid_b1.metadata = {'created_by': 'freezer',
                             'freezer_backup_id': 'f1'}
        self.assertTrue(admin.AdminOs.is_freezer_backup(valid_b1))
        self.assertEqual('f1', admin.AdminOs.get_freezer_backup_id(valid_b1))

        # Backup created in standalone mode without API (only created_by)
        valid_b2 = commons.FakeIdObject('2')
        valid_b2.metadata = {'created_by': 'freezer'}
        self.assertTrue(admin.AdminOs.is_freezer_backup(valid_b2))
        self.assertIsNone(admin.AdminOs.get_freezer_backup_id(valid_b2))

        # User backup with different created_by
        invalid_b = commons.FakeIdObject('3')
        invalid_b.metadata = {'created_by': 'user'}
        self.assertFalse(admin.AdminOs.is_freezer_backup(invalid_b))
        self.assertIsNone(admin.AdminOs.get_freezer_backup_id(invalid_b))

        # Backup without metadata
        no_meta_b = commons.FakeIdObject('4')
        no_meta_b.metadata = None
        self.assertFalse(admin.AdminOs.is_freezer_backup(no_meta_b))
        self.assertIsNone(admin.AdminOs.get_freezer_backup_id(no_meta_b))

    def test_remove_cinderbackup_older_than_freezer_only(self):
        user_backup = commons.FakeIdObject(100)
        user_backup.metadata = {}
        user_backup.is_incremental = False
        user_backup.created_at = '2020-01-01T00:00:00.000000'

        freezer_backup = commons.FakeIdObject(101)
        freezer_backup.metadata = {'created_by': 'freezer',
                                   'freezer_backup_id': 'f_uuid_101'}
        freezer_backup.is_incremental = False
        freezer_backup.created_at = '2020-01-01T00:00:00.000000'

        backups = [user_backup, freezer_backup]
        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=backups))
        self.admin_os._delete_single_backup = commons.mock.Mock(
            return_value='f_uuid_101')

        # Remove backups older than 2025 (timestamp 1735689600)
        res = self.admin_os.remove_cinderbackup_older_than(
            'vol1', 1735689600.0, freezer_only=True)

        self.assertEqual(['f_uuid_101'], res)
        self.admin_os._delete_single_backup.assert_called_once_with(101)

    def test_remove_cinderbackup_older_than_expired_chain(self):
        full_b = commons.FakeIdObject(101)
        full_b.metadata = {
            'created_by': 'freezer',
            'freezer_backup_id': 'f101'}
        full_b.is_incremental = False
        full_b.created_at = '2020-01-01T00:00:00.000000'

        inc_b = commons.FakeIdObject(102)
        inc_b.metadata = {'created_by': 'freezer', 'freezer_backup_id': 'f102'}
        inc_b.is_incremental = True
        inc_b.created_at = '2020-01-02T00:00:00.000000'

        backups = [full_b, inc_b]
        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=backups))
        delete_calls = []

        def mock_delete(bid):
            delete_calls.append(bid)
            return 'f%s' % bid

        self.admin_os._delete_single_backup = commons.mock.Mock(
            side_effect=mock_delete)

        # Cutoff is 2020-01-05 (timestamp 1578182400.0) -> entire chain expired
        res = self.admin_os.remove_cinderbackup_older_than(
            'vol1', 1578182400.0, freezer_only=True)

        self.assertEqual(['f102', 'f101'], res)
        self.assertEqual([102, 101], delete_calls)

    def test_remove_cinderbackup_older_than_active_chain_preserved(self):
        full_b = commons.FakeIdObject(101)
        full_b.metadata = {
            'created_by': 'freezer',
            'freezer_backup_id': 'f101'}
        full_b.is_incremental = False
        full_b.created_at = '2020-01-01T00:00:00.000000'

        inc_b = commons.FakeIdObject(102)
        inc_b.metadata = {'created_by': 'freezer', 'freezer_backup_id': 'f102'}
        inc_b.is_incremental = True
        inc_b.created_at = '2020-01-10T00:00:00.000000'

        backups = [full_b, inc_b]
        self.admin_os.cinder_client.backups = (
            commons.mock.Mock(return_value=backups))
        self.admin_os._delete_single_backup = commons.mock.Mock()

        # Cutoff is 2020-01-05 (timestamp 1578182400.0) -> full is old,
        # but inc is newer!
        res = self.admin_os.remove_cinderbackup_older_than(
            'vol1', 1578182400.0, freezer_only=True)

        # Whole chain should be preserved, nothing deleted
        self.assertEqual([], res)
        self.admin_os._delete_single_backup.assert_not_called()
