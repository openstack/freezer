# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P
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


"""
Freezer restore.py related tests
"""
from unittest import mock

from freezer.openstack import restore
from freezer.tests import commons


class Image(object):
    def __init__(self):
        self.id = 'test'


class TestRestore(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestRestore, self).setUp()

    def test_restore_cinder_by_glance(self):
        backup_opt = commons.BackupOpt1()
        restore.RestoreOs(backup_opt.client_manager, backup_opt.container,
                          backup_opt.storage)

    def test_restore_cinder_by_glance_from_local(self):
        backup_opt = commons.BackupOpt1()
        restore.RestoreOs(backup_opt.client_manager, backup_opt.container,
                          'local')

    def test_restore_cinder_with_backup_id(self):
        backup_opt = commons.BackupOpt1()
        ros = restore.RestoreOs(backup_opt.client_manager,
                                backup_opt.container, backup_opt.storage)
        ros.restore_cinder(35, 34, 33)

    def test_restore_cinder_without_backup_id(self):
        backup_opt = commons.BackupOpt1()
        ros = restore.RestoreOs(backup_opt.client_manager,
                                backup_opt.container, backup_opt.storage)
        ros.restore_cinder(35, 34)

    def test_restore_nova(self):
        backup_opt = commons.BackupOpt1()
        restore.RestoreOs(backup_opt.client_manager, backup_opt.container,
                          backup_opt.storage)

    def test_restore_nova_from_local(self):
        backup_opt = commons.BackupOpt1()
        restore.RestoreOs(backup_opt.client_manager, backup_opt.container,
                          'local')

    def test_restore_cinder(self):
        storage = mock.MagicMock()
        storage.type = 'swift'
        backup1 = mock.MagicMock()
        backup1.created_at = "2020-08-31T16:32:30"
        backup2 = mock.MagicMock()
        backup2.created_at = "2020-08-31T16:32:31"
        cinder_client = mock.MagicMock()
        cinder_client.backups.list.return_value = [backup1, backup2]
        cinder_client.restores.restore.return_value = 'test'
        client_manager = mock.MagicMock()
        client_manager.get_cinder.return_value = cinder_client
        restore_os = restore.RestoreOs(client_manager, '/root/test/', storage)
        result = restore_os.restore_cinder(restore_from_timestamp=1598862750)
        self.assertIsNone(result)
        result = restore_os.restore_cinder(restore_from_timestamp=1598862749)
        self.assertIsNone(result)

    @mock.patch('shutil.rmtree')
    @mock.patch('tempfile.mkdtemp')
    @mock.patch('oslo_serialization.jsonutils.load')
    @mock.patch('os.listdir')
    @mock.patch('builtins.open')
    @mock.patch('freezer.utils.utils.ReSizeStream')
    @mock.patch('freezer.utils.utils.S3ResponseStream')
    def test_create_image(self, mock_s3stream, mock_resize, mock_open,
                          mock_list, mock_load, mock_mkdtemp, mock_rmtree):
        image = Image()
        storage = mock.MagicMock()
        storage.type = 's3'
        storage.get_object.return_value = {'Body': '{"test": "test_info"}',
                                           'ContentLength': 3}
        storage.get_object_prefix.return_value = 'test'
        storage.list_all_objects.return_value = [{'Key': '/12345'},
                                                 {'Key': '/12346'}]
        client_manager = mock.MagicMock()
        client_manager.create_image.return_value = image
        restore_os = restore.RestoreOs(client_manager, '/root/test/', storage)
        result1, result2 = restore_os._create_image('/root', 12344)
        self.assertEqual(result1, {"test": "test_info"})
        self.assertEqual(result2, image)

        storage.get_object_prefix.return_value = ''
        result1, result2 = restore_os._create_image('/root', 12344)
        self.assertEqual(result1, {"test": "test_info"})
        self.assertEqual(result2, image)

        mock_open.side_effect = Exception("error")
        storage.type = 'local'
        mock_list.return_value = ['12345']
        restore_os = restore.RestoreOs(client_manager, '/root/test', storage)
        try:
            restore_os._create_image('/root', 12344)
        except BaseException as e:
            self.assertEqual(str(e), "Failed to open image file"
                                     " /root/test//root/12345//root")

        mock_open.side_effect = 'test'
        mock_load.return_value = 'test'
        result1, result2 = restore_os._create_image('/root', 12344)
        self.assertEqual(result1, 'test')
        self.assertEqual(result2, image)

        storage.type = 'ssh'
        storage.open.side_effect = Exception("error")
        storage.listdir.return_value = ['12345']
        restore_os = restore.RestoreOs(client_manager, '/root/test', storage)
        try:
            restore_os._create_image('/root', 12344)
        except BaseException as e:
            self.assertEqual(str(e), "Failed to open remote image file "
                                     "/root/test//root/12345//root")

        storage.open.side_effect = 'test'
        storage.read_metadata_file.return_value = '{"test": "test_info"}'
        restore_os = restore.RestoreOs(client_manager, '/root/test', storage)
        result1, result2 = restore_os._create_image('/root', 12344)
        self.assertEqual(result1, {"test": "test_info"})
        self.assertEqual(result2, image)

        storage.type = 'ftp'
        storage.listdir.return_value = ['12345']
        mock_mkdtemp.side_effect = Exception('error')
        restore_os = restore.RestoreOs(client_manager, '/root/test', storage)
        try:
            restore_os._create_image('/root', 12344)
        except Exception as e:
            self.assertEqual(str(e), "Unable to create a tmp directory")

        mock_mkdtemp.side_effect = "success"
        mock_rmtree.return_value = "success"
        mock_open.side_effect = 'test'
        result1, result2 = restore_os._create_image('/root', 12344)
        self.assertEqual(result1, 'test')
        self.assertEqual(result2, image)

    def test_get_backups_exception(self):
        storage = mock.MagicMock()
        storage.type = 'ss3'
        client_manager = mock.MagicMock()
        restore_os = restore.RestoreOs(client_manager, '/root/test/', storage)
        try:
            restore_os._get_backups('/root', 12347)
        except BaseException as e:
            self.assertEqual(str(e), "ss3 storage type is not supported at the"
                                     " moment. Try local, SWIFT, SSH(SFTP),"
                                     " FTP or FTPS ")

        storage = mock.MagicMock()
        storage.type = 's3'
        storage.list_all_objects.return_value = [{'Key': '/12345'},
                                                 {'Key': '/12346'}]
        restore_os = restore.RestoreOs(client_manager, '/root/test/', storage)
        try:
            restore_os._get_backups('/root', 12347)
        except BaseException as e:
            self.assertEqual(str(e), "Cannot find backups for"
                                     " path: root/test///root")
