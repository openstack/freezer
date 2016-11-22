# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import unittest

import mock
from mock import patch
from six import moves

from freezer.utils.checksum import CheckSum


class TestChecksum(unittest.TestCase):
    def setUp(self):
        self.file = mock.Mock()
        self.dir = mock.Mock()

        self.hello_world_md5sum = 'f36b2652200f5e88edd57963a1109146'
        self.hello_world_sha256sum = ('17b949eb67acf16bbf2605d57a01f7af4ff4b5'
                                      '7e200259de63fcebf20e75bbf5')

        self.fake_file = moves.StringIO(u"hello world\n")
        self.increment_hash_one = self.hello_world_sha256sum
        self.increment_hash_multi = ('1b4bc4ff41172a5f29eaeffb7e9fc24c683c693'
                                     '9ab30132ad5d93a1e4a6b16e8')
        self.increment_hash_emptydir = ("6b6c6a3d7548cc4396b3dacc6c2750c3"
                                        "da53f379d20996cbdd2c18be00c3742c")
        self.fake_dir = [('root', ['d1, .git'], ['a', 'b']), ]
        self.dir_files = ['root/a', 'root/b']
        self.exclude = "ro*b"
        self.dir_files_without_excludeds = ['root/a']
        self.dir_hashes = [
            'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447',
            'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447']
        self.dir_compute = self.increment_hash_multi
        self.file_compute = self.hello_world_sha256sum + 'onefile'

    def test_hello_world_checksum_md5(self):
        """
        Test calculating the md5 of a string
        """
        chksum = CheckSum('nofile', 'md5')
        mdsum = chksum.hashfile(self.fake_file)
        self.assertEqual(self.hello_world_md5sum, mdsum)

    def test_hello_world_checksum_sha256(self):
        """
        Test calculating the sha256 of a string
        """
        chksum = CheckSum('nofile', 'sha256')
        shasum = chksum.hashfile(self.fake_file)
        self.assertEqual(self.hello_world_sha256sum, shasum)

    def test_unknown_hasher_type(self):
        """
        Test un-known hash algorithm
        """
        with self.assertRaises(ValueError):
            CheckSum('nope', 'bulshit')

    @unittest.skipIf(sys.version_info.major == 2,
                     'Not supported on python v 2.7')
    @patch('builtins.open')
    @patch('freezer.utils.checksum.os.path.isfile')
    def test_get_hash_files(self, mock_isfile, mock_open):
        """
        Test calculating the hash of a file
        """
        mock_isfile.return_value = True
        mock_open.return_value = self.fake_file
        chksum = CheckSum('onefile')
        chksum.get_hash('onefile')
        self.assertEqual(self.increment_hash_one, chksum._increment_hash)
        chksum.get_hash('otherfile')
        self.assertEqual(self.increment_hash_multi, chksum._increment_hash)

    @patch('freezer.utils.checksum.os.path.isfile')
    def test_get_hash_multi(self, mock_isfile):
        """
        Calculate the hash of files in a directory
        """
        mock_isfile.return_value = False
        chksum = CheckSum('onedir')
        chksum.get_hash(u"./emptydir")
        self.assertEqual(self.increment_hash_emptydir, chksum._increment_hash)

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compute_dir(self, mock_hashes):
        """
        Test hashing a directory
        """
        mock_hashes.return_value = self.increment_hash_multi
        chksum = CheckSum('onedir')
        chksum.count = 2
        result = chksum.compute()
        self.assertEqual(self.dir_compute, result)

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compute_file(self, mock_get_checksum):
        """
        Test compute the checksum of a file
        """
        mock_get_checksum.return_value = self.hello_world_sha256sum
        chksum = CheckSum('onefile')
        chksum.count = 1
        result = chksum.compute()
        self.assertEqual(self.file_compute, result)

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compare_dir_match(self, mock_get_hashes):
        """
        compute checksum for a directory and it should match
        """
        mock_get_hashes.return_value = self.increment_hash_multi
        chksum = CheckSum('onedir')
        self.assertTrue(chksum.compare(self.dir_compute))

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compare_dir_not_match(self, mock_get_hashes):
        """
        compute checksum for a directory and it should not match
        """
        mock_get_hashes.return_value = self.increment_hash_multi
        chksum = CheckSum('onedir')
        self.assertFalse(chksum.compare('badchecksum'))

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compare_file_match(self, mock_get_hashes):
        """
        compute checksum for a file and it should match
        """
        mock_get_hashes.return_value = self.hello_world_sha256sum
        chksum = CheckSum('onefile')
        self.assertTrue(chksum.compare(self.file_compute))

    @patch('freezer.utils.checksum.CheckSum.get_files_hashes_in_path')
    def test_compare_file_not_match(self, mock_get_hashes):
        """
        compute checksum for a file and it should not match
        """
        mock_get_hashes.return_value = self.hello_world_sha256sum
        chksum = CheckSum('onefile')
        self.assertFalse(chksum.compare('badchecksum'))
