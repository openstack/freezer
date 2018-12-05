# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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
# from mock import patch

from freezer.storage import ftp


class BaseFtpStorageTestCase(unittest.TestCase):

    def setUp(self):
        super(BaseFtpStorageTestCase, self).setUp()
        self.ftp_opt = mock.Mock()
        self.ftp_opt.ftp_storage_path = '/just/a/path'
        self.ftp_opt.ftp_remote_pwd = 'passawd'
        self.ftp_opt.ftp_remote_username = 'usrname'
        self.ftp_opt.ftp_remote_ip = '0.0.0.0'
        self.ftp_opt.self.ftp_port = 80
        self.ftp_opt.ftp_max_segment_size = 1024

    def test_validate_BaseFtpStorage(self):
        with self.assertRaises(Exception) as cm:  # noqa
            ftp.FtpStorage(
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
            ftp.FtpStorage(
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
            ftp.FtpStorage(
                storage_path=self.ftp_opt.ftp_storage_path,
                remote_pwd=None,
                remote_username=self.ftp_opt.ftp_remote_username,
                remote_ip=self.ftp_opt.ftp_remote_ip,
                port=self.ftp_opt.ftp_port,
                max_segment_size=self.ftp_opt.ftp_max_segment_size)
            the_exception = cm.exception
            self.assertIn('Please provide remote password',
                          str(the_exception))
