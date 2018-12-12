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

# import mock
# from mock import patch

from freezer.utils import crypt


class AESCipherTestCase(unittest.TestCase):

    def setUp(self):
        super(AESCipherTestCase, self).setUp()
        self.passwd_test_file_dir = None
        self.passwd_test_file_name = None
        self.create_pass_test_file()

    def tearDown(self):
        super(AESCipherTestCase, self).tearDown()
        self.delete_pass_test_file()

    def create_pass_test_file(self):
        if self.passwd_test_file_name:
            return
        tmpdir = tempfile.mkdtemp()
        FILES_DIR_PREFIX = "freezer_passwd_dir"
        files_dir = tempfile.mkdtemp(dir=tmpdir, prefix=FILES_DIR_PREFIX)
        file_name = "passwd_test"
        self.passwd_test_file_dir = files_dir
        text = '78f40f2c57eee727a4be179049cecf89'
        filehandle = open(files_dir + "/" + file_name, 'w')
        if filehandle:
            filehandle.write(text)
            filehandle.close()
            self.passwd_test_file_name = files_dir + "/" + file_name

    def delete_pass_test_file(self):
        if self.passwd_test_file_name:
            files_dir = self.passwd_test_file_dir
            shutil.rmtree(files_dir)
            self.passwd_test_file_name = None
            self.passwd_test_file_dir = None

    def test_get_pass_from_file(self):
        pfile = self.passwd_test_file_name
        passwd = crypt.AESCipher._get_pass_from_file(pfile)
        self.assertEqual(passwd, '78f40f2c57eee727a4be179049cecf89')

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    def test_derive_key_and_iv(self):
        passwd = 'ababab'
        salt = 'a'
        ret1, ret2 = crypt.AESCipher._derive_key_and_iv(password=passwd,
                                                        salt=salt,
                                                        key_length=10,
                                                        iv_length=5)
        expect1 = '\xb3J5\xce\xd4b\x87\xce\xe0:'
        expect2 = '\x93\xc9\x9d\x03\x00'
        self.assertEqual(ret1, expect1)
        self.assertEqual(ret2, expect2)
