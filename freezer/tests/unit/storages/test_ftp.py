# (c) Copyright 2018 ZTE Corporation.
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

import shutil
import sys
import tempfile
import unittest

import mock

from freezer.storage import ftp
from mock import patch


class BaseFtpStorageTestCase(unittest.TestCase):

    def setUp(self):
        super(BaseFtpStorageTestCase, self).setUp()
        self.ftp_opt = mock.Mock()
        self.ftp_opt.ftp_storage_path = '/just/a/path'
        self.ftp_opt.ftp_remote_pwd = 'passawd'
        self.ftp_opt.ftp_remote_username = 'usrname'
        self.ftp_opt.ftp_remote_ip = '0.0.0.0'
        self.ftp_opt.ftp_port = 2121
        self.ftp_opt.ftp_max_segment_size = 1024

    def test_validate_BaseFtpStorage(self):
        with self.assertRaises(Exception) as cm:  # noqa
            ftp.BaseFtpStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=self.ftp_opt.ftp_remote_pwd,
                remote_ip=None,
                remote_username=self.ftp_opt.ftp_remote_username,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size)
            the_exception = cm.exception
            self.assertIn('Please provide --ftp-host value',
                          str(the_exception))

        with self.assertRaises(Exception) as cm:  # noqa
            ftp.BaseFtpStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=self.ftp_opt.ftp_remote_pwd,
                remote_ip=self.ftp_opt.ftp_remote_ip,
                remote_username=None,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size)
            the_exception = cm.exception
            self.assertIn('Please provide --ftp-username value',
                          str(the_exception))

        with self.assertRaises(Exception) as cm:  # noqa
            ftp.BaseFtpStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=None,
                remote_username=self.ftp_opt.ftp_remote_username,
                remote_ip=self.ftp_opt.ftp_remote_ip,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size)
            the_exception = cm.exception
            self.assertIn('Please provide remote password',
                          str(the_exception))


class FtpStorageTestCase(unittest.TestCase):

    def setUp(self):
        super(FtpStorageTestCase, self).setUp()
        self.ftp_opt = mock.Mock()
        self.ftp_opt.ftp_storage_path = '/just/a/path'
        self.ftp_opt.ftp_remote_pwd = 'passawd'
        self.ftp_opt.ftp_remote_username = 'usrname'
        self.ftp_opt.ftp_remote_ip = '0.0.0.0'
        self.ftp_opt.ftp_port = 2121
        self.ftp_test_file_dir = None
        self.ftp_test_file_name = None

    def create_ftp_test_file(self):
        if self.ftp_test_file_name:
            return
        tmpdir = tempfile.mkdtemp()
        FILES_DIR_PREFIX = "freezer_ftptest_files_dir"
        files_dir = tempfile.mkdtemp(dir=tmpdir, prefix=FILES_DIR_PREFIX)
        file_name = "file_ftp_test"
        self.ftp_test_file_dir = files_dir
        text = "FTPTESTTXT"
        filehandle = open(files_dir + "/" + file_name, 'w')
        if filehandle:
            filehandle.write(text)
            filehandle.close()
            self.ftp_test_file_name = file_name

    def delete_ftp_test_file(self):
        if self.ftp_test_file_name:
            files_dir = self.ftp_test_file_dir
            shutil.rmtree(files_dir)
            self.ftp_test_file_name = None
            self.ftp_test_file_dir = None

    def create_ftpstorage_obj(self):
        obj = ftp.FtpStorage(
            storage_path=self.ftp_opt.ftp_storage_path,
            remote_pwd=self.ftp_opt.ftp_remote_pwd,
            remote_username=self.ftp_opt.ftp_remote_username,
            remote_ip=self.ftp_opt.ftp_remote_ip,
            port=self.ftp_opt.ftp_port,
            max_segment_size=self.ftp_opt.ftp_max_segment_size)
        return obj

    @patch('ftplib.FTP')
    def test_init_fail_raise_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        seffect = mock.Mock(side_effect=Exception('create ftp failed error'))
        mock_ftp.raiseError.side_effect = seffect
        with self.assertRaises(Exception) as cm:  # noqa
            self.create_ftpstorage_obj()
            the_exception = cm.exception
            self.assertIn('create ftp failed error',
                          str(the_exception))

    @patch('ftplib.FTP')
    def test_init_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        self.create_ftpstorage_obj()
        self.assertTrue(mock_ftp.set_pasv.called)
        self.assertTrue(mock_ftp.connect.called)
        self.assertTrue(mock_ftp.login.called)
        self.assertTrue(mock_ftp.nlst.called)
        mock_ftp.set_pasv.assert_called_with(True)
        mock_ftp.connect.assert_called_with(self.ftp_opt.ftp_remote_ip,
                                            self.ftp_opt.ftp_port, 60)
        mock_ftp.login.assert_called_with(self.ftp_opt.ftp_remote_username,
                                          self.ftp_opt.ftp_remote_pwd)

    @patch('tempfile.mkdtemp')
    @patch('ftplib.FTP')
    def test_create_tempdir_FtpStorage(self, mock_ftp_constructor,
                                       mock_tempfile_constructor):
        mock_tempfile = mock_tempfile_constructor.return_value
        ftp_obj = self.create_ftpstorage_obj()
        tmp = ftp_obj._create_tempdir()
        self.assertEqual(tmp, mock_tempfile)

    @patch('ftplib.FTP')
    def test_listdir_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        test_dir = '/home/test'
        filelist = ['test1.py', 'test2.py', 'readme.txt', 'ftp.sh']
        mock_ftp.nlst.return_value = filelist
        ret = ftpobj.listdir(test_dir)
        self.assertTrue(mock_ftp.nlst.called)
        mock_ftp.cwd.assert_called_with(test_dir)
        self.assertEqual(sorted(filelist), ret)

    @patch('ftplib.FTP')
    def test_listdir_fail_raise_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        test_dir = '/home/test'
        seffect = mock.Mock(side_effect=Exception())
        mock_ftp.raiseError.side_effect = seffect
        ret = ftpobj.listdir(test_dir)
        self.assertEqual(list(), ret)

    @patch('ftplib.FTP')
    def test_putfile_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        self.create_ftp_test_file()
        frompath = self.ftp_test_file_dir + "/" + self.ftp_test_file_name
        topath = '/home/to'
        ftpobj.put_file(frompath, topath)
        self.assertTrue(mock_ftp.pwd.called)
        self.assertTrue(mock_ftp.storbinary.called)
        self.delete_ftp_test_file()

    @patch('ftplib.FTP')
    def test_getfile_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        self.create_ftp_test_file()
        topath = self.ftp_test_file_dir + "/" + self.ftp_test_file_name
        frompath = '/home/from'
        ftpobj.get_file(frompath, topath)
        self.assertTrue(mock_ftp.pwd.called)
        self.assertTrue(mock_ftp.retrbinary.called)
        self.delete_ftp_test_file()

    @patch('ftplib.FTP')
    def test_create_dirs_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        path = '/'
        ftpobj.create_dirs(path)
        mock_ftp.cwd.assert_called_with(path)
        path = '/home'
        ftpobj.create_dirs(path)
        mock_ftp.cwd.assert_called_with(path)

    @patch('ftplib.FTP')
    def test_rmtree_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftpobj = self.create_ftpstorage_obj()
        path = '/home/tecs'
        ftpobj.rmtree(path)
        self.assertTrue(mock_ftp.dir.called)
        self.assertTrue(mock_ftp.rmd.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("freezer.storage.ftp.BaseFtpStorage.create_dirs")
    @patch("freezer.storage.ftp.BaseFtpStorage.put_file")
    @patch("__builtin__.open")
    @patch('ftplib.FTP')
    def test_write_backup_FtpStorage(self, mock_ftp_constructor,
                                     mock_open,
                                     mock_put_file,
                                     mock_create_dirs):
        ftpobj = self.create_ftpstorage_obj()

        rich_queue = mock.MagicMock()
        rich_queue.get_messages = mock.MagicMock()
        rich_queue.get_messages.return_value = ['1']

        backup = mock.MagicMock()
        backup.copy = mock.MagicMock()
        backup.copy.return_value = backup

        path = 'fakepath'
        backup.data_path = mock.MagicMock()
        backup.data_path.return_value = path

        b_file = mock.MagicMock()
        b_file.write = mock.MagicMock()

        mock_open = mock.MagicMock()
        mock_open.return_value = b_file

        ftpobj.write_backup(rich_queue=rich_queue,
                            backup=backup)
        self.assertTrue(mock_create_dirs.called)
        self.assertTrue(mock_put_file.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("freezer.storage.ftp.BaseFtpStorage.create_dirs")
    @patch("freezer.storage.ftp.BaseFtpStorage.put_file")
    @patch("__builtin__.open")
    @patch('ftplib.FTP')
    def test_add_stream_FtpStorage(self, mock_ftp_constructor,
                                   mock_open,
                                   mock_put_file,
                                   mock_create_dirs):
        ftpobj = self.create_ftpstorage_obj()

        rich_queue = mock.MagicMock()
        rich_queue.get_messages = mock.MagicMock()
        rich_queue.get_messages.return_value = ['1']

        package_name = 'fakedir/fakename'
        stream = ['fakestream']

        backup = mock.MagicMock()
        backup.copy = mock.MagicMock()
        backup.copy.return_value = backup

        b_file = mock.MagicMock()
        b_file.write = mock.MagicMock()

        mock_open = mock.MagicMock()
        mock_open.return_value = b_file

        ftpobj.add_stream(stream=stream,
                          package_name=package_name)

        self.assertTrue(mock_create_dirs.called)
        self.assertTrue(mock_put_file.called)


class FtpsStorageTestCase(unittest.TestCase):

    def setUp(self):
        super(FtpsStorageTestCase, self).setUp()
        self.ftp_opt = mock.Mock()
        self.ftp_opt.ftp_storage_path = '/just/a/path'
        self.ftp_opt.ftp_remote_pwd = 'passawd'
        self.ftp_opt.ftp_remote_username = 'usrname'
        self.ftp_opt.ftp_remote_ip = '0.0.0.0'
        self.ftp_opt.ftp_port = 2121
        self.ftp_opt.ftp_keyfile = '/just/key.pem'
        self.ftp_opt.ftp_certfile = '/just/cert.pem'

    def create_ftpsStorage_obj(self):
        obj = ftp.FtpsStorage(
            storage_path=self.ftp_opt.ftp_storage_path,
            remote_pwd=self.ftp_opt.ftp_remote_pwd,
            remote_username=self.ftp_opt.ftp_remote_username,
            remote_ip=self.ftp_opt.ftp_remote_ip,
            port=self.ftp_opt.ftp_port,
            max_segment_size=self.ftp_opt.ftp_max_segment_size,
            keyfile=self.ftp_opt.ftp_keyfile,
            certfile=self.ftp_opt.ftp_certfile)
        return obj

    def test_init_fail_FtpsStorage(self):
        with self.assertRaises(Exception) as cm:  # noqa
            self.create_ftpsStorage_obj()
            the_exception = cm.exception
            self.assertIn('create ftp failed error',
                          str(the_exception))

    @patch('ftplib.FTP_TLS')
    def test_init_ok_FtpsStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        self.create_ftpsStorage_obj()
        self.assertTrue(mock_ftp.set_pasv.called)
        self.assertTrue(mock_ftp.connect.called)
        self.assertTrue(mock_ftp.login.called)
        self.assertTrue(mock_ftp.prot_p.called)
        self.assertTrue(mock_ftp.nlst.called)
        mock_ftp.set_pasv.assert_called_with(True)
        mock_ftp.connect.assert_called_with(self.ftp_opt.ftp_remote_ip,
                                            self.ftp_opt.ftp_port, 60)
        mock_ftp.login.assert_called_with(self.ftp_opt.ftp_remote_username,
                                          self.ftp_opt.ftp_remote_pwd)
