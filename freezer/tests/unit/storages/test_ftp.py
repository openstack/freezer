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

    def test_init_fail_FtpStorage(self):
        with self.assertRaises(Exception) as cm:  # noqa
            ftp.FtpStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=self.ftp_opt.ftp_remote_pwd,
                remote_username=self.ftp_opt.ftp_remote_username,
                remote_ip=self.ftp_opt.ftp_remote_ip,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size)
            the_exception = cm.exception
            self.assertIn('create ftp failed error',
                          str(the_exception))

    @patch('ftplib.FTP')
    def test_init_ok_FtpStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftp.FtpStorage(
            storage_path=self.ftp_opt.ftp_storage_path,
            remote_pwd=self.ftp_opt.ftp_remote_pwd,
            remote_username=self.ftp_opt.ftp_remote_username,
            remote_ip=self.ftp_opt.ftp_remote_ip,
            port=self.ftp_opt.ftp_port,
            max_segment_size=self.ftp_opt.ftp_max_segment_size)
        self.assertTrue(mock_ftp.set_pasv.called)
        self.assertTrue(mock_ftp.connect.called)
        self.assertTrue(mock_ftp.login.called)
        self.assertTrue(mock_ftp.nlst.called)
        mock_ftp.set_pasv.assert_called_with(True)
        mock_ftp.connect.assert_called_with(self.ftp_opt.ftp_remote_ip,
                                            self.ftp_opt.ftp_port, 60)
        mock_ftp.login.assert_called_with(self.ftp_opt.ftp_remote_username,
                                          self.ftp_opt.ftp_remote_pwd)


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

    def test_init_fail_FtpsStorage(self):
        with self.assertRaises(Exception) as cm:  # noqa
            ftp.FtpsStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=self.ftp_opt.ftp_remote_pwd,
                remote_username=self.ftp_opt.ftp_remote_username,
                remote_ip=self.ftp_opt.ftp_remote_ip,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size,
                keyfile=self.ftp_opt.ftp_keyfile,
                certfile=self.ftp_opt.ftp_certfile)
            the_exception = cm.exception
            self.assertIn('create ftp failed error',
                          str(the_exception))

    @patch('ftplib.FTP_TLS')
    def test_init_ok_FtpsStorage(self, mock_ftp_constructor):
        mock_ftp = mock_ftp_constructor.return_value
        ftp.FtpsStorage(
            storage_path=self.ftp_opt.ftp_storage_path,
            remote_pwd=self.ftp_opt.ftp_remote_pwd,
            remote_username=self.ftp_opt.ftp_remote_username,
            remote_ip=self.ftp_opt.ftp_remote_ip,
            port=self.ftp_opt.ftp_port,
            max_segment_size=self.ftp_opt.ftp_max_segment_size,
            keyfile=self.ftp_opt.ftp_keyfile,
            certfile=self.ftp_opt.ftp_certfile)
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
