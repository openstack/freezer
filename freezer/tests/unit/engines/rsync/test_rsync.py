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
        self.relpath = '/home/tecs'
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

    def get_rsync_data_struct(self):

        file_mode = 2
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
        size = 1024
        devmajor = 15
        devminor = 5
        level_id = '1111'

        header_len = 128
        file_path = 'fakefilepath'
        data_ver = 1
        rsync_block_size = 'fakersyncblocksize'
        rm = '1112'
        link_name = 'fakelink_name'

        header_list = [header_len, file_path, data_ver, file_mode, uid,
                       gid, size, mtime, ctime, uname, gname, file_type,
                       link_name, inumber, nlink, devminor, devmajor,
                       rsync_block_size, level_id, rm]

        file_header = '124\x00/home/tecs\x001\x00w\x00fakeuid' \
                      '\x00fakegid\x001024\x002\x001\x00tecs' \
                      '\x00admin\x00u\x00\x00fakeinumber\x00fakenlink' \
                      '\x005\x0015\x004096' \
                      '\x001111\x000000'

        files_meta = {
            'files': {},
            'directories': {},
            'meta': {
                'broken_links_tot': '',
                'total_files': '',
                'total_directories': '',
                'backup_size_on_disk': 0,
                'backup_size_uncompressed': 0,
                'backup_size_compressed': 0,
                'platform': sys.platform
            },
            'abs_backup_path': 'fakepath',
            'broken_links': [],
            'rsync_struct_ver': 1,
            'rsync_block_size': 4096}

        old_file_meta = {
            'files': {},
            'directories': {},
            'meta': {
                'broken_links_tot': '',
                'total_files': '',
                'total_directories': '',
                'backup_size_on_disk': 0,
                'backup_size_uncompressed': 2,
                'backup_size_compressed': 1,
                'platform': sys.platform
            },
            'abs_backup_path': 'fakepath',
            'broken_links': [],
            'rsync_struct_ver': 1,
            'rsync_block_size': 4096}

        inode_dict_struct = {
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

        inode_str_struct = (
            b'{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}\00{}\00{}\00{}').format(
            1, file_mode,
            uid, gid, size, mtime, ctime, uname, gname,
            file_type, lname, inumber, nlink, devminor, devmajor,
            4096, level_id, '0000')

        self.inode_str_struct = inode_str_struct
        self.inode_dict_struct = inode_dict_struct
        self.files_meta = files_meta
        self.file_header = file_header
        self.old_file_meta = old_file_meta
        self.header_list = header_list

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
        fspath = self.relpath
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
        fs_path = self.relpath
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
        fs_path = self.relpath
        new_level = True
        fake_rsync = self.mock_rsync
        file_mode = 'w'
        file_type = 's'
        lname = ''
        mock_oslstat.return_value = mock.MagicMock()
        mock_oslstat.return_value.st_mode = file_mode

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
        fs_path = self.relpath
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
        mock_osmajor.return_value = devmajor

        devminor = 'fakedevminor'
        mock_osminor.return_value = devminor

        level_id = '1111'

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
        mock_pwd_getpwuid.return_value = [uname, 0, 0]

        mock_grp_getgrgid.return_value = [gname, 0, 0]

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
        file_path = self.relpath
        self.get_rsync_data_struct()
        inode_bin_str = self.inode_str_struct
        fake_rsync = self.mock_rsync

        res = '98\x00/home/tecs\x001\x002\x00fakeuid' \
              '\x00fakegid\x001024\x002\x001\x00tecs' \
              '\x00admin\x00u\x00\x00fakeinumber\x00fakenlink' \
              '\x005\x0015\x004096' \
              '\x001111\x000000'

        ret = fake_rsync.gen_file_header(file_path=file_path,
                                         inode_str_struct=inode_bin_str)
        self.assertEqual(ret, res)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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

        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'k'
        header_list[19] = 'fakerm'
        header_list[18] = '0000'

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 0
        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'k'
        header_list[19] = '1111'
        header_list[18] = '0000'

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'd'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]
        file_mode = header_list[3]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        level_id = '0000'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'r'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]
        size = header_list[6]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = True

        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'b'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]
        devminor = header_list[15]
        devmajor = header_list[16]
        file_mode = header_list[3]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = True

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'c'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]
        devminor = header_list[15]
        devmajor = header_list[16]
        file_mode = header_list[3]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = True

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'p'
        header_list[19] = '1112'
        header_list[18] = '0000'
        uname = header_list[9]
        gname = header_list[10]
        mtime = header_list[7]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = True

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'l'
        header_list[19] = '1112'
        header_list[18] = '0000'
        link_name = header_list[12]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = True

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'd'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

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

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
    def test_make_files_filetype_b_exception(self, mock_os_path_isdir,
                                             mock_os_path_exists,
                                             mock_make_reg_file,
                                             mock_os_makedirs,
                                             mock_os_makedev,
                                             mock_os_mknod,
                                             mock_os_mkfifo,
                                             mock_os_symlink,
                                             mock_set_inode,
                                             mock_os_unlink):
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'b'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        mock_os_makedev.side_effect = OSError
        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
    def test_make_files_filetype_c_exception(self, mock_os_path_isdir,
                                             mock_os_path_exists,
                                             mock_make_reg_file,
                                             mock_os_makedirs,
                                             mock_os_makedev,
                                             mock_os_mknod,
                                             mock_os_mkfifo,
                                             mock_os_symlink,
                                             mock_set_inode,
                                             mock_os_unlink):
        file_path = 'fakefilepath'
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'c'
        header_list[19] = '1112'
        header_list[18] = '0000'
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        mock_os_makedev.side_effect = OSError

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
    def test_make_files_filetype_p_exception(self, mock_os_path_isdir,
                                             mock_os_path_exists,
                                             mock_make_reg_file,
                                             mock_os_makedirs,
                                             mock_os_makedev,
                                             mock_os_mknod,
                                             mock_os_mkfifo,
                                             mock_os_symlink,
                                             mock_set_inode,
                                             mock_os_unlink):
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'p'
        header_list[19] = '1112'
        file_path = header_list[1]
        mtime = header_list[7]
        uname = header_list[9]
        gname = header_list[10]
        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = True

        fileabspath = '{0}/{1}'.format(restore_abs_path, file_path)

        mock_os_mkfifo.side_effect = OSError

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        mock_set_inode.assert_called_once_with(uname, gname,
                                               mtime, fileabspath)
        self.assertEqual(ret, data_chunk)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
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
    def test_make_files_filetype_l_exception(self, mock_os_path_isdir,
                                             mock_os_path_exists,
                                             mock_make_reg_file,
                                             mock_os_makedirs,
                                             mock_os_makedev,
                                             mock_os_mknod,
                                             mock_os_mkfifo,
                                             mock_os_symlink,
                                             mock_set_inode,
                                             mock_os_unlink):
        self.get_rsync_data_struct()
        header_list = self.header_list
        header_list[11] = 'l'
        header_list[19] = '1112'

        read_pipe = 'fakeread_pipe'
        data_chunk = 'fakedatachunk'
        restore_abs_path = self.relpath
        flushed = 'True'
        current_backup_level = 1

        fake_rsync = self.mock_rsync

        mock_os_path_isdir.return_value = False

        mock_os_path_exists.return_value = True

        mock_os_symlink.side_effect = OSError

        ret = fake_rsync.make_files(header_list=header_list,
                                    restore_abs_path=restore_abs_path,
                                    read_pipe=read_pipe,
                                    data_chunk=data_chunk,
                                    flushed=flushed,
                                    current_backup_level=current_backup_level)
        self.assertEqual(ret, data_chunk)

    def test_process_backup_data(self):
        data = 'fakedata'
        do_compress = True

        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        fake_rsync.cipher = self.cipher

        fake_rsync.encrypt_pass_file = True

        fake_rsync.compressor.compress = mock.MagicMock()
        fake_rsync.compressor.compress.return_value = data

        fake_rsync.cipher.encrypt = mock.MagicMock()
        fake_rsync.cipher.encrypt.return_value = data

        ret = fake_rsync.process_backup_data(data=data,
                                             do_compress=do_compress)
        self.assertEqual(ret, data)

    def test_process_backup_data_compress(self):
        data = 'fakedata'
        do_compress = True

        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        fake_rsync.cipher = self.cipher

        fake_rsync.encrypt_pass_file = False

        fake_rsync.compressor.compress = mock.MagicMock()
        fake_rsync.compressor.compress.return_value = data

        ret = fake_rsync.process_backup_data(data=data,
                                             do_compress=do_compress)
        self.assertEqual(ret, data)

    def test_process_backup_data_encrypt(self):
        data = 'fakedata'
        do_compress = False

        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        fake_rsync.cipher = self.cipher

        fake_rsync.encrypt_pass_file = True

        fake_rsync.cipher.encrypt = mock.MagicMock()
        fake_rsync.cipher.encrypt.return_value = data

        ret = fake_rsync.process_backup_data(data=data,
                                             do_compress=do_compress)
        self.assertEqual(ret, data)

    def test_process_restore_data(self):
        data = 'fakedata'

        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        fake_rsync.cipher = self.cipher

        fake_rsync.encrypt_pass_file = False

        fake_rsync.compressor.decompress = mock.MagicMock()
        fake_rsync.compressor.decompress.return_value = data

        ret = fake_rsync.process_restore_data(data=data)
        self.assertEqual(ret, data)

    def test_process_restore_data_encrypt(self):
        data = 'fakedata'

        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        fake_rsync.cipher = self.cipher

        fake_rsync.encrypt_pass_file = True

        fake_rsync.compressor.decompress = mock.MagicMock()
        fake_rsync.compressor.decompress.return_value = data

        fake_rsync.cipher.decrypt = mock.MagicMock()
        fake_rsync.cipher.decrypt.return_value = data

        ret = fake_rsync.process_restore_data(data=data)
        self.assertEqual(ret, data)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("__builtin__.open")
    @patch('os.path.lexists')
    @patch('os.path.exists')
    @patch('freezer.engine.rsync.pyrsync.blockchecksums')
    def test_compute_checksums_regfile_true(self, mock_blockchecksums,
                                            mock_os_path_exists,
                                            mock_os_path_lexists,
                                            mock_open):
        rel_path = 'rel_path'
        fake_rsync = self.mock_rsync

        files_meta = {'files': {'rel_path': {'signature': [1, 2]}}}
        files_meta1 = {'files': {'rel_path': {'signature': [3, 4]}}}

        file_path_fd = mock.MagicMock()
        file_path_fd.return_value = 'fakehandle'

        mock_open.return_value = file_path_fd

        mock_blockchecksums.return_value = [3, 4]

        ret = fake_rsync.compute_checksums(rel_path=rel_path,
                                           files_meta=files_meta,
                                           reg_file=True)

        self.assertEqual(ret, files_meta1)

    @patch('os.path.lexists')
    @patch('os.path.exists')
    def test_compute_checksums_regfile_False(self, mock_os_path_exists,
                                             mock_os_path_lexists):
        rel_path = 'rel_path'
        fake_rsync = self.mock_rsync

        files_meta = {'files': {'rel_path': {'signature': [1, 2]}}}
        files_meta1 = {'files': {'rel_path': {'signature': [[], []]}}}

        mock_os_path_lexists.return_value = True

        mock_os_path_exists.return_value = True

        ret = fake_rsync.compute_checksums(rel_path=rel_path,
                                           files_meta=files_meta,
                                           reg_file=False)

        self.assertEqual(ret, files_meta1)

    @patch('os.path.lexists')
    @patch('os.path.exists')
    def test_compute_checksums_regfile_raise(self, mock_os_path_exists,
                                             mock_os_path_lexists):
        rel_path = 'rel_path'
        fake_rsync = self.mock_rsync
        reg_file = False

        mock_os_path_lexists.return_value = True

        mock_os_path_exists.return_value = False

        self.assertRaises(IOError,
                          fake_rsync.compute_checksums,
                          rel_path,
                          reg_file)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("__builtin__.open")
    @patch('os.path.lexists')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.rsync_gen_delta')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.process_backup_data')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.compute_checksums')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_file_modified')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_old_file_meta')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_reg_file')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.gen_file_header')
    def test_compute_incrementals_ok(self, mock_gen_file_header,
                                     mock_is_reg_file,
                                     mock_get_old_file_meta,
                                     mock_is_file_modified,
                                     mock_compute_checksums,
                                     mock_process_backup_data,
                                     mock_rsync_gen_delta,
                                     mock_os_path_lexists,
                                     mock_open):
        rel_path = self.relpath
        frsync = self.mock_rsync
        self.get_rsync_data_struct()
        deleted = False
        file_header = self.file_header
        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()

        mock_gen_file_header.return_value = file_header

        mock_is_reg_file.return_value = True
        files_meta = self.files_meta
        old_fsmetastruct = self.old_file_meta

        mock_get_old_file_meta.return_value = self.old_file_meta

        mock_is_file_modified.return_value = True

        mock_compute_checksums.return_value = files_meta

        file_path_fd = mock.MagicMock()
        file_path_fd.return_value = 'fakehandle'
        file_path_fd.close = mock.MagicMock()
        file_path_fd.read = mock.MagicMock()

        mock_open.return_value = file_path_fd
        inode_dict_struct = self.inode_dict_struct
        inode_str_struct = self.inode_str_struct

        ret = frsync.compute_incrementals(rel_path=rel_path,
                                          inode_str_struct=inode_str_struct,
                                          inode_dict_struct=inode_dict_struct,
                                          files_meta=files_meta,
                                          old_fs_meta_struct=old_fsmetastruct,
                                          write_queue=write_queue,
                                          deleted=deleted)
        self.assertEqual(ret, files_meta)
        mock_open.assert_called_with(rel_path)
        self.assertTrue(mock_process_backup_data.called)
        self.assertTrue(write_queue.put.called)
        self.assertTrue(file_path_fd.close.called)
        self.assertTrue(mock_rsync_gen_delta.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("__builtin__.open")
    @patch('os.path.lexists')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.rsync_gen_delta')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.process_backup_data')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.compute_checksums')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_file_modified')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_old_file_meta')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_reg_file')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.gen_file_header')
    def test_compute_incrementals_no_oldmeta(self, mock_gen_file_header,
                                             mock_is_reg_file,
                                             mock_get_old_file_meta,
                                             mock_is_file_modified,
                                             mock_compute_checksums,
                                             mock_process_backup_data,
                                             mock_rsync_gen_delta,
                                             mock_os_path_lexists,
                                             mock_open):
        rel_path = self.relpath
        frsync = self.mock_rsync
        self.get_rsync_data_struct()
        deleted = False
        file_header = self.file_header
        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()

        mock_gen_file_header.return_value = file_header

        mock_is_reg_file.return_value = True
        files_meta = self.files_meta
        old_fsmetastruct = self.old_file_meta

        mock_get_old_file_meta.return_value = None

        mock_is_file_modified.return_value = True

        mock_compute_checksums.return_value = files_meta

        file_path_fd = mock.MagicMock()
        file_path_fd.return_value = 'fakehandle'
        file_path_fd.close = mock.MagicMock()
        file_path_fd.read = mock.MagicMock()
        data_block = ['1', '2', None]
        file_path_fd.read.side_effect = data_block
        mock_open.return_value = file_path_fd
        inode_dict_struct = self.inode_dict_struct
        inode_str_struct = self.inode_str_struct

        ret = frsync.compute_incrementals(rel_path=rel_path,
                                          inode_str_struct=inode_str_struct,
                                          inode_dict_struct=inode_dict_struct,
                                          files_meta=files_meta,
                                          old_fs_meta_struct=old_fsmetastruct,
                                          write_queue=write_queue,
                                          deleted=deleted)
        self.assertEqual(ret, files_meta)
        mock_open.assert_called_with(rel_path)
        self.assertTrue(mock_process_backup_data.called)
        self.assertTrue(write_queue.put.called)
        self.assertTrue(file_path_fd.close.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch("__builtin__.open")
    @patch('os.path.lexists')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.rsync_gen_delta')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.process_backup_data')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.compute_checksums')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_file_modified')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_old_file_meta')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.is_reg_file')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.gen_file_header')
    def test_compute_incrementals_exception(self, mock_gen_file_header,
                                            mock_is_reg_file,
                                            mock_get_old_file_meta,
                                            mock_is_file_modified,
                                            mock_compute_checksums,
                                            mock_process_backup_data,
                                            mock_rsync_gen_delta,
                                            mock_os_path_lexists,
                                            mock_open):
        rel_path = self.relpath
        frsync = self.mock_rsync
        self.get_rsync_data_struct()
        deleted = False

        file_header = self.file_header
        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()

        mock_gen_file_header.return_value = file_header

        mock_is_reg_file.return_value = True
        files_meta = self.files_meta
        old_fsmetastruct = self.old_file_meta

        mock_get_old_file_meta.side_effect = OSError

        mock_is_file_modified.return_value = True
        mock_os_path_lexists.return_value = False
        inode_dict_struct = self.inode_dict_struct
        inode_str_struct = self.inode_str_struct

        ret = frsync.compute_incrementals(rel_path=rel_path,
                                          inode_str_struct=inode_str_struct,
                                          inode_dict_struct=inode_dict_struct,
                                          files_meta=files_meta,
                                          old_fs_meta_struct=old_fsmetastruct,
                                          write_queue=write_queue,
                                          deleted=deleted)
        self.assertEqual(ret, files_meta)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch('os.path.isdir')
    @patch('os.path.relpath')
    @patch('os.path.getsize')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.process_backup_data')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.compute_incrementals')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_file_struct')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_old_file_meta')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.gen_file_header')
    def test_process_file_is_dir_true(self, mock_gen_file_header,
                                      mock_get_old_file_meta,
                                      mock_get_file_struct,
                                      mock_compute_incrementals,
                                      mock_process_backup_data,
                                      mock_os_path_getsize,
                                      mock_os_path_relpath,
                                      mock_os_path_isdir):
        file_path = 'fakefilepath'
        rel_path = 'fakerelpath'
        fs_path = 'fakefspath'
        frsync = self.mock_rsync
        self.get_rsync_data_struct()
        file_header = self.file_header

        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()

        mock_gen_file_header.return_value = file_header
        files_meta = self.files_meta
        old_fsmetastruct = self.old_file_meta

        mock_get_old_file_meta.return_value = True
        mock_os_path_relpath.return_value = rel_path
        inode_dict_struct = self.inode_dict_struct
        inode_str_struct = self.inode_str_struct

        mock_get_file_struct.return_value = inode_dict_struct, inode_str_struct
        mock_os_path_isdir.return_value = True

        frsync.process_file(file_path=file_path,
                            fs_path=fs_path,
                            files_meta=files_meta,
                            old_fs_meta_struct=old_fsmetastruct,
                            write_queue=write_queue)

        mock_os_path_relpath.assert_called_with(file_path, fs_path)
        mock_get_old_file_meta.assert_called_with(old_fsmetastruct, rel_path)
        mock_get_file_struct.assert_called_with(rel_path, True)
        mock_os_path_isdir.assert_called_with(file_path)
        mock_os_path_getsize.assert_called_with(rel_path)
        mock_gen_file_header.assert_called_with(rel_path, inode_str_struct)
        mock_process_backup_data.assert_called_with(file_header)
        self.assertTrue(write_queue.put.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch('os.path.isdir')
    @patch('os.path.relpath')
    @patch('os.path.getsize')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.process_backup_data')
    @patch('freezer.engine.rsync.rsync.'
           'RsyncEngine.compute_incrementals')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_file_struct')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.get_old_file_meta')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.gen_file_header')
    def test_process_file_is_dir_False(self, mock_gen_file_header,
                                       mock_get_old_file_meta,
                                       mock_get_file_struct,
                                       mock_compute_incrementals,
                                       mock_process_backup_data,
                                       mock_os_path_getsize,
                                       mock_os_path_relpath,
                                       mock_os_path_isdir):
        file_path = 'fakefilepath'
        rel_path = 'fakerelpath'
        fs_path = 'fakefspath'
        self.get_rsync_data_struct()
        frsync = self.mock_rsync
        file_header = self.file_header

        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()

        mock_gen_file_header.return_value = file_header
        files_meta = self.files_meta

        old_fsmetastruct = self.old_file_meta

        mock_get_old_file_meta.return_value = True
        mock_os_path_relpath.return_value = rel_path
        inode_dict_struct = self.inode_dict_struct
        inode_str_struct = self.inode_str_struct

        mock_get_file_struct.return_value = inode_dict_struct, inode_str_struct
        mock_os_path_isdir.return_value = False
        mock_compute_incrementals.return_value = files_meta

        frsync.process_file(file_path=file_path,
                            fs_path=fs_path,
                            files_meta=files_meta,
                            old_fs_meta_struct=old_fsmetastruct,
                            write_queue=write_queue)

        mock_os_path_relpath.assert_called_with(file_path, fs_path)
        mock_get_old_file_meta.assert_called_with(old_fsmetastruct, rel_path)
        mock_get_file_struct.assert_called_with(rel_path, True)
        mock_os_path_isdir.assert_called_with(file_path)
        mock_compute_incrementals.assert_called_with(rel_path,
                                                     inode_str_struct,
                                                     inode_dict_struct,
                                                     files_meta,
                                                     old_fsmetastruct,
                                                     write_queue)

    @patch('os.path.isfile')
    def test_get_fs_meta_struct_isnot_file(self, mock_os_path_isfile):
        fs_meta_path = self.relpath
        fs_meta_struct = {}
        fake_rsync = self.mock_rsync
        mock_os_path_isfile.return_value = False
        ret = fake_rsync.get_fs_meta_struct(fs_meta_path=fs_meta_path)
        self.assertEqual(ret, fs_meta_struct)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'gen_struct_for_deleted_files')
    @patch('freezer.utils.compress.one_shot_compress')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'process_backup_data')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.process_file')
    @patch('os.walk')
    @patch('os.getcwd')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'get_fs_meta_struct')
    @patch('freezer.utils.compress.Compressor.flush')
    @patch('os.path.isdir')
    @patch("__builtin__.open")
    def test_get_sign_delta_isnot_dir(self, mock_open,
                                      mock_os_path_isdir,
                                      mock_flush,
                                      mock_get_fs_meta_struct,
                                      mock_os_getcwd,
                                      mock_os_walk,
                                      mock_process_file,
                                      mock_process_backup_data,
                                      mock_one_shot_compress,
                                      mock_gen_struct_for_deleted_files):

        files_meta = {
            'files': {},
            'directories': {},
            'meta': {
                'broken_links_tot': '',
                'total_files': '',
                'total_directories': '',
                'backup_size_on_disk': 0,
                'backup_size_uncompressed': 0,
                'backup_size_compressed': 0,
                'platform': sys.platform
            },
            'abs_backup_path': self.relpath,
            'broken_links': [],
            'rsync_struct_ver': 1,
            'rsync_block_size': 4096}

        fs_path = self.relpath
        manifest_path = self.relpath
        flushed_data = 'fakedata'
        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        mock_flush.return_value = flushed_data
        old_files_meta = files_meta

        mock_get_fs_meta_struct.return_value = old_files_meta
        mock_os_path_isdir.return_value = False
        mock_os_getcwd.return_value = self.relpath

        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()
        mock_process_backup_data.return_value = flushed_data

        manifest_file = mock.MagicMock()
        manifest_file.write = mock.MagicMock()
        mock_open.return_value = manifest_file

        fake_rsync.get_sign_delta(fs_path=fs_path,
                                  manifest_path=manifest_path,
                                  write_queue=write_queue)

        mock_get_fs_meta_struct.assert_called_with(manifest_path)
        self.assertTrue(mock_process_file.called)
        self.assertTrue(mock_process_backup_data.called)

    @unittest.skipIf(sys.version_info.major == 3,
                     'Not supported on python v 3.x')
    @patch('os.chdir')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'gen_struct_for_deleted_files')
    @patch('freezer.utils.compress.one_shot_compress')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'process_backup_data')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.process_file')
    @patch('os.walk')
    @patch('os.getcwd')
    @patch('freezer.engine.rsync.rsync.RsyncEngine.'
           'get_fs_meta_struct')
    @patch('freezer.utils.compress.Compressor.flush')
    @patch('os.path.isdir')
    @patch("__builtin__.open")
    def test_get_sign_delta_is_dir(self, mock_open,
                                   mock_os_path_isdir,
                                   mock_flush,
                                   mock_get_fs_meta_struct,
                                   mock_os_getcwd,
                                   mock_os_walk,
                                   mock_process_file,
                                   mock_process_backup_data,
                                   mock_one_shot_compress,
                                   mock_gen_struct_for_deleted_files,
                                   mock_os_chdir):

        fs_path = self.relpath
        manifest_path = self.relpath
        flushed_data = 'fakedata'
        fake_rsync = self.mock_rsync
        fake_rsync.compressor = self.compressor
        mock_flush.return_value = flushed_data
        old_files_meta = None

        mock_get_fs_meta_struct.return_value = old_files_meta
        mock_os_path_isdir.return_value = True
        mock_os_getcwd.return_value = self.relpath

        write_queue = mock.MagicMock()
        write_queue.put = mock.MagicMock()
        mock_process_backup_data.return_value = flushed_data

        manifest_file = mock.MagicMock()
        manifest_file.write = mock.MagicMock()
        mock_open.return_value = manifest_file
        fake_rsync.get_sign_delta(fs_path=fs_path,
                                  manifest_path=manifest_path,
                                  write_queue=write_queue)

        mock_get_fs_meta_struct.assert_called_with(manifest_path)
        self.assertTrue(mock_process_backup_data.called)
