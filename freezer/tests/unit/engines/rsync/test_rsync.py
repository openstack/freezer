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
import sys
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

    @patch('grp.getgrnam')
    @patch('pwd.getpwnam')
    @patch('os.utime')
    @patch('os.chown')
    def test_set_inode_ok(self, mock_oschown,
                          mock_osutime,
                          mock_pwd_getpwnam,
                          mock_grp_getgrnam):
        uname = 'adminu'
        gname = 'adming'
        mtime = 20181230
        name = 'tecs'
        current_uid = 1
        current_gid = 2
        fake_rsync = self.mock_rsync
        mock_pwd_getpwnam.return_value = mock.MagicMock()
        mock_pwd_getpwnam.return_value.pw_uid = current_uid
        mock_grp_getgrnam.return_value = mock.MagicMock()
        mock_grp_getgrnam.return_value.gr_gid = current_gid

        fake_rsync.set_inode(uname=uname,
                             gname=gname,
                             mtime=mtime,
                             name=name)
        mock_pwd_getpwnam.assert_called_with(uname)
        mock_grp_getgrnam.assert_called_with(gname)
        mock_oschown.assert_called_with(name, current_uid, current_gid)
        mock_osutime.assert_called_with(name, (mtime, mtime))

    @patch('getpass.getuser')
    @patch('grp.getgrnam')
    @patch('pwd.getpwnam')
    @patch('os.utime')
    @patch('os.chown')
    def test_set_inode_raise_exception(self, mock_oschown,
                                       mock_osutime,
                                       mock_pwd_getpwnam,
                                       mock_grp_getgrnam,
                                       mock_getpass_getuser):
        uname = 'adminu'
        gname = 'adming'
        mtime = 20181230
        name = 'tecs'
        current_uid = 1
        current_gid = 2
        fake_rsync = self.mock_rsync
        mock_pwd_getpwnam.return_value = mock.MagicMock()
        mock_pwd_getpwnam.return_value.pw_uid = current_uid
        mock_grp_getgrnam.return_value = mock.MagicMock()
        mock_grp_getgrnam.return_value.gr_gid = current_gid

        mock_osutime.side_effect = OSError
        self.assertRaises(Exception,   # noqa
                          fake_rsync.set_inode,
                          uname=uname,
                          gname=gname,
                          mtime=mtime,
                          name=name)
        self.assertTrue(mock_getpass_getuser.called)

    @patch('os.lstat')
    def test_get_file_struct_raise_exception(self, mock_oslstat):
        fs_path = '/home/tecs'
        new_level = True
        fake_rsync = self.mock_rsync
        mock_oslstat.side_effect = OSError
        self.assertRaises(Exception,    # noqa
                          fake_rsync.get_file_struct,
                          fs_path=fs_path,
                          new_level=new_level)

    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_file_type')
    @patch('os.minor')
    @patch('os.major')
    @patch('grp.getgrgid')
    @patch('pwd.getpwuid')
    @patch('os.lstat')
    def test_get_file_struct_s_ok(self, mock_oslstat,
                                  mock_pwd_getpwuid,
                                  mock_grp_getgrgid,
                                  mock_osmajor,
                                  mock_osminor,
                                  mock_getfiletype):
        fs_path = '/home/tecs'
        new_level = True
        fake_rsync = self.mock_rsync
        file_mode = 'w'
        file_type = 's'
        lname = ''
        mock_oslstat.return_value = mock.MagicMock()
        mock_oslstat.return_value.st_mode = file_mode

        mock_getfiletype.return_value = mock.MagicMock()
        mock_getfiletype.return_value = file_type, lname
        ret1, ret2 = fake_rsync.get_file_struct(fs_path=fs_path,
                                                new_level=new_level)
        self.assertEqual(ret1, False)
        self.assertEqual(ret2, False)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_file_type')
    @patch('os.minor')
    @patch('os.major')
    @patch('grp.getgrgid')
    @patch('pwd.getpwuid')
    @patch('os.lstat')
    def test_get_file_struct_u_ok(self, mock_oslstat,
                                  mock_pwd_getpwuid,
                                  mock_grp_getgrgid,
                                  mock_osmajor,
                                  mock_osminor,
                                  mock_getfiletype):
        fs_path = '/home/tecs'
        new_level = True
        fake_rsync = self.mock_rsync
        file_mode = 'w'
        file_type = 'u'
        lname = ''
        ctime = 1
        mtime = 2
        uname = 'tecs'
        gname = 'admin'
        dev = 'fakedev'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 'fakezise'

        mock_oslstat.return_value = mock.MagicMock()
        mock_oslstat.return_value.st_mode = file_mode
        mock_oslstat.return_value.st_ctime = int(ctime)
        mock_oslstat.return_value.st_mtime = int(mtime)
        mock_oslstat.return_value.st_dev = dev
        mock_oslstat.return_value.st_ino = inumber
        mock_oslstat.return_value.st_nlink = nlink
        mock_oslstat.return_value.st_uid = uid
        mock_oslstat.return_value.st_gid = gid
        mock_oslstat.return_value.st_size = size

        devmajor = 'fakedevmajor'
        mock_osmajor.return_value = mock.MagicMock()
        mock_osmajor.return_value = devmajor

        devminor = 'fakedevminor'
        mock_osminor.return_value = mock.MagicMock()
        mock_osminor.return_value = devminor

        level_id = '1111'

        mock_getfiletype.return_value = mock.MagicMock()
        mock_getfiletype.return_value = file_type, lname

        inode_dict = {
            'inode': {
                'inumber': inumber,
                'nlink': nlink,
                'mode': file_mode,
                'uid': uid,
                'gid': gid,
                'size': size,
                'devmajor': devmajor,
                'devminor': devminor,
                'mtime': mtime,
                'ctime': ctime,
                'uname': uname,
                'gname': gname,
                'ftype': file_type,
                'lname': lname,
                'rsync_block_size': 4096,
                'level_id': level_id,
                'deleted': '0000'
            }
        }

        inode_bin_str = (
            b'{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}\00{}\00{}\00{}').format(
            1, file_mode,
            uid, gid, size, mtime, ctime, uname, gname,
            file_type, lname, inumber, nlink, devminor, devmajor,
            4096, level_id, '0000')

        mock_pwd_getpwuid.return_value = mock.MagicMock()
        mock_pwd_getpwuid.return_value = [uname, 0, 0]

        mock_grp_getgrgid.return_value = mock.MagicMock()
        mock_grp_getgrgid.return_value = [gname, 0, 0]

        mock_getfiletype.return_value = mock.MagicMock()
        mock_getfiletype.return_value = file_type, lname
        self.maxDiff = None
        ret1, ret2 = fake_rsync.get_file_struct(fs_path=fs_path,
                                                new_level=new_level)
        self.assertEqual(ret1, inode_dict)
        self.assertEqual(ret2, inode_bin_str)
