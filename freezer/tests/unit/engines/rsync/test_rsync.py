# (C) Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import unittest

from freezer.engine.rsync import rsync
from mock import patch


class TestRsyncEngine(unittest.TestCase):
    def setUp(self):
        super(TestRsyncEngine, self).setUp()
        self.compression_algo = 'gzip'
        self.encrypt_file = '/home/tecs'
        self.symlinks = None
        self.exclude = False
        self.storage = 'local'
        self.is_windows = False
        self.dry_run = False
        self.max_segment_size = 1024
        # Compression and encryption objects
        self.compressor = mock.MagicMock()
        self.cipher = mock.MagicMock()
        self.name = "rsync"
        self.mock_rsync = rsync.RsyncEngine(compression=self.compression_algo,
                                            symlinks=self.symlinks,
                                            exclude=self.exclude,
                                            storage=self.storage,
                                            max_segment_size=1024,
                                            encrypt_key=self.encrypt_file)

    def test_metadata(self):
        ret = self.mock_rsync.metadata()
        expect = {
            "engine_name": self.name,
            "compression": self.compression_algo,
            "encryption": bool(self.encrypt_file)
        }
        self.assertEqual(ret, expect)

    def test_is_reg_file(self):
        filetype = 'r'
        ret = rsync.RsyncEngine.is_reg_file(file_type=filetype)
        self.assertEqual(ret, True)
        filetype = 'u'
        ret = rsync.RsyncEngine.is_reg_file(file_type=filetype)
        self.assertEqual(ret, True)
        filetype = 'a'
        ret = rsync.RsyncEngine.is_reg_file(file_type=filetype)
        self.assertEqual(ret, False)

    def test_is_file_modified(self):
        oldfilemeta = mock.MagicMock()
        oldfilemeta['inode']['mtime'] = 1
        oldfilemeta['inode']['ctime'] = 2

        filemeta = mock.MagicMock()
        filemeta['inode']['mtime'] = 3
        filemeta['inode']['ctime'] = 4

        ret = rsync.RsyncEngine.is_file_modified(old_file_meta=oldfilemeta,
                                                 file_meta=filemeta)
        self.assertEqual(ret, True)

        oldfilemeta['inode']['mtime'] = 1
        oldfilemeta['inode']['ctime'] = 2

        filemeta['inode']['mtime'] = 1
        filemeta['inode']['ctime'] = 4

        ret = rsync.RsyncEngine.is_file_modified(old_file_meta=oldfilemeta,
                                                 file_meta=filemeta)

    @patch('os.readlink')
    @patch('stat.S_ISSOCK')
    @patch('stat.S_ISFIFO')
    @patch('stat.S_ISBLK')
    @patch('stat.S_ISCHR')
    @patch('stat.S_ISLNK')
    @patch('stat.S_ISDIR')
    @patch('stat.S_ISREG')
    def test_get_file_type(self, mock_stat_reg,
                           mock_stat_dir,
                           mock_stat_link,
                           mock_stat_chr,
                           mock_stat_blk,
                           mock_stat_fifo,
                           mock_stat_sock,
                           mock_os_readlink):
        filemode = 'w'
        fspath = '/home/tecs'
        mock_os_readlink.return_value = 'tecs'
        mock_stat_reg.return_value = True
        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'r')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = True
        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'd')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = True

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'l')
        self.assertEqual(ret2, 'tecs')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = False
        mock_stat_chr.return_value = True

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'c')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = False
        mock_stat_chr.return_value = False
        mock_stat_blk.return_value = True

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'b')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = False
        mock_stat_chr.return_value = False
        mock_stat_blk.return_value = False
        mock_stat_fifo.return_value = True

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'p')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = False
        mock_stat_chr.return_value = False
        mock_stat_blk.return_value = False
        mock_stat_fifo.return_value = False
        mock_stat_sock.return_value = True

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 's')
        self.assertEqual(ret2, '')

        mock_stat_reg.return_value = False
        mock_stat_dir.return_value = False
        mock_stat_link.return_value = False
        mock_stat_chr.return_value = False
        mock_stat_blk.return_value = False
        mock_stat_fifo.return_value = False
        mock_stat_sock.return_value = False

        ret1, ret2 = rsync.RsyncEngine.get_file_type(file_mode=filemode,
                                                     fs_path=fspath)
        self.assertEqual(ret1, 'u')
        self.assertEqual(ret2, '')
