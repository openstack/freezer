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
import shutil
import stat
import sys
import tempfile
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
        self.rsync_test_file_name = None
        self.rsync_test_file_dir = None
        self.mock_rsync = rsync.RsyncEngine(compression=self.compression_algo,
                                            symlinks=self.symlinks,
                                            exclude=self.exclude,
                                            storage=self.storage,
                                            max_segment_size=1024,
                                            encrypt_key=self.encrypt_file)

    def create_rsync_test_file(self):
        if self.rsync_test_file_name:
            return
        tmpdir = tempfile.mkdtemp()
        FILES_DIR_PREFIX = "freezer_rsynctest_files_dir"
        files_dir = tempfile.mkdtemp(dir=tmpdir, prefix=FILES_DIR_PREFIX)
        file_name = "file_rsync_test"
        self.rsync_test_file_dir = files_dir
        text = "rsyncTESTTXT"
        filehandle = open(files_dir + "/" + file_name, 'w')
        if filehandle:
            filehandle.write(text)
            filehandle.close()
            self.rsync_test_file_name = file_name

    def delete_rsync_test_file(self):
        if self.rsync_test_file_name:
            files_dir = self.rsync_test_file_dir
            shutil.rmtree(files_dir)
            self.rsync_test_file_name = None
            self.rsync_test_file_dir = None

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

    @patch('freezer.engine.rsync.rsync.RsyncEngine.write_file')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.write_changes_in_file')
    def test_make_reg_file_0000_level(self, mock_write_changes_in_file,
                                      mock_write_file):
        size = 1024
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        flushed = 'True'
        level_id = '0000'

        fake_rsync = self.mock_rsync
        self.create_rsync_test_file()
        file_dir = self.rsync_test_file_dir
        file_name = self.rsync_test_file_name
        file_path = file_dir + "/" + file_name
        mock_write_file.return_value = mock.MagicMock()
        mock_write_file.return_value = data_chunk

        ret = fake_rsync.make_reg_file(size=size,
                                       file_path=file_path,
                                       read_pipe=read_pipe,
                                       data_chunk=data_chunk,
                                       flushed=flushed,
                                       level_id=level_id)
        self.delete_rsync_test_file()
        self.assertEqual(ret, data_chunk)

    @patch('freezer.engine.rsync.rsync.RsyncEngine.write_file')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.write_changes_in_file')
    def test_make_reg_file_1111_level(self, mock_write_changes_in_file,
                                      mock_write_file):
        size = 1024
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        flushed = 'False'
        level_id = '1111'
        self.create_rsync_test_file()
        file_dir = self.rsync_test_file_dir
        file_name = self.rsync_test_file_name
        file_path = file_dir + "/" + file_name
        fake_rsync = self.mock_rsync

        mock_write_changes_in_file.return_value = mock.MagicMock()
        mock_write_changes_in_file.return_value = data_chunk

        ret = fake_rsync.make_reg_file(size=size,
                                       file_path=file_path,
                                       read_pipe=read_pipe,
                                       data_chunk=data_chunk,
                                       flushed=flushed,
                                       level_id=level_id)

        self.delete_rsync_test_file()
        self.assertEqual(ret, data_chunk)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    def test_gen_file_header(self):
        file_path = '/home/tecs'

        file_mode = 'w'
        file_type = 'u'
        lname = ''
        ctime = 1
        mtime = 2
        uname = 'tecs'
        gname = 'admin'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 'fakezise'
        devmajor = 'fakedevmajor'

        devminor = 'fakedevminor'
        level_id = '1111'

        inode_bin_str = (
            b'{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}\00{}\00{}\00{}').format(
            1, file_mode,
            uid, gid, size, mtime, ctime, uname, gname,
            file_type, lname, inumber, nlink, devminor, devmajor,
            4096, level_id, '0000')

        fake_rsync = self.mock_rsync

        res = '124\x00/home/tecs\x001\x00w\x00fakeuid' \
              '\x00fakegid\x00fakezise\x002\x001\x00tecs' \
              '\x00admin\x00u\x00\x00fakeinumber\x00fakenlink' \
              '\x00fakedevminor\x00fakedevmajor\x004096' \
              '\x001111\x000000'

        ret = fake_rsync.gen_file_header(file_path=file_path,
                                         inode_str_struct=inode_bin_str)
        self.assertEqual(ret, res)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files(self, mock_os_path_isdir,
                        mock_os_path_exists,
                        mock_make_reg_file,
                        mock_os_makedirs,
                        mock_os_makedev,
                        mock_os_mknod,
                        mock_os_mkfifo,
                        mock_os_symlink,
                        mock_set_inode,
                        mock_os_unlink):

        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'fakefile_type'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 'fakedevminor'
        devmajor = 'fakedevmajor'
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = 'fakerm'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 0

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_os_unlink.assert_called_with(fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_rm_1111(self, mock_os_path_isdir,
                                mock_os_path_exists,
                                mock_make_reg_file,
                                mock_os_makedirs,
                                mock_os_makedev,
                                mock_os_mknod,
                                mock_os_mkfifo,
                                mock_os_symlink,
                                mock_set_inode,
                                mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'fakefile_type'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 'fakedevminor'
        devmajor = 'fakedevmajor'
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1111'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_os_unlink.assert_called_once_with(fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_d_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'd'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 'fakedevminor'
        devmajor = 'fakedevmajor'
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_os_makedirs.assert_called_once_with(fileabspath, file_mode)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_r_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'r'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 'fakedevminor'
        devmajor = 'fakedevmajor'
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        mock_make_reg_file.return_value = mock.MagicMock()
        mock_make_reg_file.return_value = data_chunk

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)

        mock_make_reg_file.assert_called_once_with(size,
                                                   fileabspath,
                                                   read_pipe,
                                                   data_chunk,
                                                   flushed,
                                                   level_id)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_b_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'b'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 5
        devmajor = 10
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        file_mode |= stat.S_IFBLK

        mock_os_makedev.return_value = mock.MagicMock()
        new_dev = 'fakenewdev'
        mock_os_makedev.return_value = new_dev

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)

        mock_os_makedev.assert_called_once_with(devmajor, devminor)
        mock_os_mknod.assert_called_once_with(fileabspath, file_mode,
                                              new_dev)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_c_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'c'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 5
        devmajor = 10
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        file_mode |= stat.S_IFCHR

        mock_os_makedev.return_value = mock.MagicMock()
        new_dev = 'fakenewdev'
        mock_os_makedev.return_value = new_dev

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)

        mock_os_makedev.assert_called_once_with(devmajor, devminor)
        mock_os_mknod.assert_called_once_with(fileabspath, file_mode,
                                              new_dev)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_p_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'p'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 5
        devmajor = 10
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)

        mock_os_mkfifo.assert_called_once_with(fileabspath)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_l_ok(self, mock_os_path_isdir,
                                      mock_os_path_exists,
                                      mock_make_reg_file,
                                      mock_os_makedirs,
                                      mock_os_makedev,
                                      mock_os_mknod,
                                      mock_os_mkfifo,
                                      mock_os_symlink,
                                      mock_set_inode,
                                      mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'l'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 5
        devmajor = 10
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)

        mock_os_symlink.assert_called_once_with(link_name, fileabspath)
        self.assertEqual(ret, data_chunk)

    @patch('os.unlink')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.set_inode')
    @patch('os.symlink')
    @patch('os.mkfifo')
    @patch('os.mknod')
    @patch('os.makedev')
    @patch('os.makedirs')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.make_reg_file')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_make_files_filetype_d_exception(self, mock_os_path_isdir,
                                             mock_os_path_exists,
                                             mock_make_reg_file,
                                             mock_os_makedirs,
                                             mock_os_makedev,
                                             mock_os_mknod,
                                             mock_os_mkfifo,
                                             mock_os_symlink,
                                             mock_set_inode,
                                             mock_os_unlink):
        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        file_mode = 2
        uid = 'fakeuid'
        gid = 'fakegid'
        size = 1024
        mtime = 20181230
        ctime = 20180302
        uname = 'fakeuname'
        gname = 'fakegname'
        file_type = 'd'
        link_name = 'fakelink_name'
        inumber = 'fakeinumber'
        nlink = 'fakenlink'
        devminor = 'fakedevminor'
        devmajor = 'fakedevmajor'
        rsync_block_size = 'fakersyncblocksize'
        level_id = '0000'
        rm = '1112'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = '/home/tecs'
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = mock.MagicMock()
        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = mock.MagicMock()
        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        mock_os_makedirs.side_effect = OSError

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)
