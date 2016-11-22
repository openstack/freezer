"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import unittest

import mock
from mock import patch

from freezer.snapshot import lvm


class Test_lvm_snap_remove(unittest.TestCase):
    @patch('freezer.snapshot.lvm.os')
    @patch('freezer.snapshot.lvm._umount')
    @patch('freezer.snapshot.lvm._lvremove')
    def test_return_none_on_success(self, mock_lvremove, mock_umount, mock_os):
        backup_opt = mock.Mock()
        backup_opt.lvm_volgroup = 'one'
        backup_opt.lvm_snapname = 'two'
        self.assertIsNone(lvm.lvm_snap_remove(backup_opt))


class Test_lvm_snap(unittest.TestCase):
    @patch('freezer.snapshot.lvm.get_lvm_info')
    @patch('freezer.snapshot.lvm.utils.create_dir')
    def test_with_snapshot_opt_simple_sets_correct_path_and_raises_on_perm(
            self, mock_create_dir, mock_get_lvm_info):
        mock_get_lvm_info.return_value = {
            'volgroup': 'lvm_volgroup',
            'srcvol': 'lvm_device',
            'snap_path': 'snap_path'}

        backup_opt = mock.Mock()
        backup_opt.snapshot = True
        backup_opt.path_to_backup = '/just/a/path'
        backup_opt.lvm_dirmount = '/var/mountpoint'
        backup_opt.lvm_snapperm = 'invalid_value'

        with self.assertRaises(Exception) as cm:  # noqa
            lvm.lvm_snap(backup_opt)
        the_exception = cm.exception
        self.assertIn('Invalid value for option lvm-snap-perm',
                      str(the_exception))

    @patch('freezer.snapshot.lvm.validate_lvm_params')
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.get_vol_fs_type')
    @patch('freezer.snapshot.lvm.get_lvm_info')
    @patch('freezer.snapshot.lvm.utils.create_dir')
    def test_ok(self, mock_create_dir, mock_get_lvm_info, mock_get_vol_fs_type,
                mock_popen, mock_validate_lvm_params):
        mock_get_lvm_info.return_value = {
            'volgroup': 'lvm_volgroup',
            'srcvol': 'lvm_device',
            'snap_path': 'snap_path'}
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        backup_opt = mock.Mock()
        backup_opt.snapshot = True
        backup_opt.path_to_backup = '/just/a/path'
        backup_opt.lvm_dirmount = '/var/mountpoint'
        backup_opt.lvm_snapperm = 'ro'
        backup_opt.lvm_volgroup = ''
        backup_opt.lvm_srcvol = ''
        backup_opt.lvm_snapsize = '1G'

        self.assertTrue(lvm.lvm_snap(backup_opt))

    @patch('freezer.snapshot.lvm.validate_lvm_params')
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.get_vol_fs_type')
    @patch('freezer.snapshot.lvm.get_lvm_info')
    @patch('freezer.utils.utils.create_dir')
    def test_snapshot_fails(self, mock_create_dir, mock_get_lvm_info,
                            mock_get_vol_fs_type, mock_popen,
                            mock_validate_lvm_params):
        mock_get_lvm_info.return_value = {
            'volgroup': 'lvm_volgroup',
            'srcvol': 'lvm_device',
            'snap_path': 'snap_path'}
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        backup_opt = mock.Mock()
        backup_opt.snapshot = True
        backup_opt.path_to_backup = '/just/a/path'
        backup_opt.lvm_dirmount = '/var/mountpoint'
        backup_opt.lvm_snapperm = 'ro'
        backup_opt.lvm_snapsize = '1G'

        with self.assertRaises(Exception) as cm:  # noqa
            lvm.lvm_snap(backup_opt)
        the_exception = cm.exception
        self.assertIn('lvm snapshot creation error', str(the_exception))

    @patch('freezer.snapshot.lvm.lvm_snap_remove')
    @patch('freezer.snapshot.lvm.validate_lvm_params')
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.get_vol_fs_type')
    @patch('freezer.snapshot.lvm.get_lvm_info')
    @patch('freezer.utils.utils.create_dir')
    def test_already_mounted(self, mock_create_dir, mock_get_lvm_info,
                             mock_get_vol_fs_type,
                             mock_popen, mock_validate_lvm_params,
                             lvm_snap_remove):
        mock_get_vol_fs_type.return_value = 'xfs'
        mock_get_lvm_info.return_value = {
            'volgroup': 'lvm_volgroup',
            'srcvol': 'lvm_device',
            'snap_path': 'snap_path'}
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', 'already mounted'
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        backup_opt = mock.Mock()
        backup_opt.snapshot = True
        backup_opt.path_to_backup = '/just/a/path'
        backup_opt.lvm_dirmount = '/var/mountpoint'
        backup_opt.lvm_snapperm = 'ro'
        backup_opt.lvm_snapsize = '1G'

        self.assertTrue(lvm.lvm_snap(backup_opt))

    @patch('freezer.snapshot.lvm.lvm_snap_remove')
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.get_vol_fs_type')
    @patch('freezer.snapshot.lvm.get_lvm_info')
    @patch('freezer.snapshot.lvm.utils.create_dir')
    def test_snapshot_mount_error_raises_Exception(self,
                                                   mock_create_dir,
                                                   mock_get_lvm_info,
                                                   mock_get_vol_fs_type,
                                                   mock_popen,
                                                   mock_lvm_snap_remove):
        mock_get_vol_fs_type.return_value = 'xfs'
        mock_get_lvm_info.return_value = {
            'volgroup': 'lvm_volgroup',
            'srcvol': 'lvm_device',
            'snap_path': 'snap_path'}
        mock_lvcreate_process, mock_mount_process = mock.Mock(), mock.Mock()

        mock_lvcreate_process.communicate.return_value = '', ''
        mock_lvcreate_process.returncode = 0

        mock_mount_process.communicate.return_value = '', 'mount error'
        mock_mount_process.returncode = 1

        mock_popen.side_effect = [mock_lvcreate_process, mock_mount_process]

        backup_opt = mock.Mock()
        backup_opt.snapshot = True
        backup_opt.path_to_backup = '/just/a/path'
        backup_opt.lvm_dirmount = '/var/mountpoint'
        backup_opt.lvm_snapperm = 'ro'
        backup_opt.lvm_snapsize = '1G'

        with self.assertRaises(Exception) as cm:  # noqa
            lvm.lvm_snap(backup_opt)
        the_exception = cm.exception
        self.assertIn('lvm snapshot mounting error', str(the_exception))

        mock_lvm_snap_remove.assert_called_once_with(backup_opt)


# class Test_get_lvm_info(unittest.TestCase):
#     @patch('freezer.snapshot.lvm.lvm_guess')
#     @patch('freezer.snapshot.lvm.utils.get_mount_from_path')
#     def test_using_guess(self, mock_get_mount_from_path, mock_lvm_guess):
#         mock_get_mount_from_path.return_value = ('/home/somedir',
#                                                  'some-snap-path')
#         mock_lvm_guess.return_value = 'vg_test', 'lv_test', 'lvm_device'
#         mounts = (
#             '/dev/mapper/vg_prova-lv_prova_vol1 /home/pippo ext4 rw,'
#             'relatime,data=ordered 0 0'
#         )
#         mocked_open_function = mock.mock_open(read_data=mounts)
#
#         with patch("__builtin__.open", mocked_open_function):
#             res = lvm.get_lvm_info('lvm_auto_snap_value')
#
#         expected_result = {'volgroup': 'vg_test',
#                            'snap_path': 'some-snap-path',
#                            'srcvol': 'lvm_device'}
#         self.assertEqual(res, expected_result)
#
#     @patch('freezer.snapshot.lvm.subprocess.Popen')
#     @patch('freezer.snapshot.lvm.lvm_guess')
#     @patch('freezer.snapshot.lvm.utils.get_mount_from_path')
#     def test_using_mount(self, mock_get_mount_from_path, mock_lvm_guess,
#                          mock_popen):
#         mock_get_mount_from_path.return_value = ('/home/somedir',
#                                                  'some-snap-path')
#         mock_lvm_guess.side_effect = [(None, None, None),
#                                       ('vg_test', 'lv_test', 'lvm_device')]
#         mounts = (
#             '/dev/mapper/vg_prova-lv_prova_vol1 /home/pippo ext4 rw,'
#             'relatime,data=ordered 0 0'
#         )
#         mocked_open_function = mock.mock_open(read_data=mounts)
#         mock_process = mock.Mock()
#         mock_process.returncode = 0
#         mock_popen.return_value = mock_process
#         mock_process.communicate.return_value = '', ''
#
#         with patch("__builtin__.open", mocked_open_function):
#             res = lvm.get_lvm_info('lvm_auto_snap_value')
#
#         expected_result = {'volgroup': 'vg_test',
#                            'snap_path': 'some-snap-path',
#                            'srcvol': 'lvm_device'}
#         self.assertEqual(res, expected_result)
#
#     @patch('freezer.snapshot.lvm.subprocess.Popen')
#     @patch('freezer.snapshot.lvm.lvm_guess')
#     @patch('freezer.snapshot.lvm.utils.get_mount_from_path')
#     def test_raises_Exception_when_info_not_found(
#             self, mock_get_mount_from_path, mock_lvm_guess, mock_popen):
#         mock_get_mount_from_path.return_value = ('/home/somedir',
#                                                  'some-snap-path')
#         mock_lvm_guess.return_value = None, None, None
#         mounts = (
#             '/dev/mapper/vg_prova-lv_prova_vol1 /home/pippo ext4 rw,'
#             'relatime,data=ordered 0 0'
#         )
#         mocked_open_function = mock.mock_open(read_data=mounts)
#         mock_process = mock.Mock()
#         mock_lvm_guess.return_value = None, None, None
#         mock_process.communicate.return_value = '', ''
#         mock_popen.return_value = mock_process
#
#         with patch("__builtin__.open", mocked_open_function):
#             self.assertRaises(Exception, lvm.get_lvm_info,
#                               'lvm_auto_snap_value')


class Test_lvm_guess(unittest.TestCase):
    def test_no_match(self):
        mount_points = []
        mount_point_path = '/home/pippo'
        source = '/proc/mounts'

        res = lvm.lvm_guess(mount_point_path, mount_points, source)

        expected_result = (None, None, None)
        self.assertEqual(res, expected_result)

    def test_unsing_proc_mounts(self):
        mount_points = [
            'rootfs / rootfs rw 0 0\n',
            'sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0\n',
            'proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0\n',
            'udev /dev devtmpfs rw,relatime,size=2010616k,nr_inodes=502654,'
            'mode=755 0 0\n',
            'devpts /dev/pts devpts rw,nosuid,noexec,relatime,gid=5,mode=620,'
            'ptmxmode=000 0 0\n',
            'tmpfs /run tmpfs rw,nosuid,noexec,relatime,size=404836k,mode=755 '
            '0 0\n',
            '/dev/mapper/fabuntu--vg-root / ext4 rw,relatime,'
            'errors=remount-ro,data=ordered 0 0\n',
            'none /sys/fs/cgroup tmpfs rw,relatime,size=4k,mode=755 0 0\n',
            'none /sys/fs/fuse/connections fusectl rw,relatime 0 0\n',
            'none /sys/kernel/debug debugfs rw,relatime 0 0\n',
            'none /sys/kernel/security securityfs rw,relatime 0 0\n',
            'cgroup /sys/fs/cgroup/cpuset cgroup rw,relatime,cpuset 0 0\n',
            'cgroup /sys/fs/cgroup/cpu cgroup rw,relatime,cpu 0 0\n',
            'cgroup /sys/fs/cgroup/cpuacct cgroup rw,relatime,cpuacct 0 0\n',
            'cgroup /sys/fs/cgroup/memory cgroup rw,relatime,memory 0 0\n',
            'none /run/lock tmpfs rw,nosuid,nodev,noexec,relatime,size=5120k '
            '0 0\n',
            'none /run/shm tmpfs rw,nosuid,nodev,relatime 0 0\n',
            'none /run/user tmpfs rw,nosuid,nodev,noexec,relatime,'
            'size=102400k,mode=755 0 0\n',
            'cgroup /sys/fs/cgroup/devices cgroup rw,relatime,devices 0 0\n',
            'none /sys/fs/pstore pstore rw,relatime 0 0\n',
            'cgroup /sys/fs/cgroup/freezer cgroup rw,relatime,freezer 0 0\n',
            'cgroup /sys/fs/cgroup/blkio cgroup rw,relatime,blkio 0 0\n',
            'cgroup /sys/fs/cgroup/perf_event cgroup rw,relatime,perf_event '
            '0 0\n',
            'cgroup /sys/fs/cgroup/hugetlb cgroup rw,relatime,hugetlb 0 0\n',
            '/dev/sda1 /boot ext2 rw,relatime 0 0\n',
            'systemd /sys/fs/cgroup/systemd cgroup rw,nosuid,nodev,noexec,'
            'relatime,name=systemd 0 0\n',
            '/dev/mapper/vg_prova-lv_prova_vol1 /home/pippo ext4 rw,relatime,'
            'data=ordered 0 0\n'
        ]
        mount_point_path = '/home/pippo'
        source = '/proc/mounts'

        res = lvm.lvm_guess(mount_point_path, mount_points, source)

        expected_result = (
            'vg_prova', 'lv_prova_vol1', '/dev/vg_prova/lv_prova_vol1')
        self.assertEqual(res, expected_result)

    def test_unsing_mount(self):
        mount_points = [
            '/dev/mapper/fabuntu--vg-root on / type ext4 (rw,errors='
            'remount-ro)',
            'proc on /proc type proc (rw,noexec,nosuid,nodev)',
            'sysfs on /sys type sysfs (rw,noexec,nosuid,nodev)',
            'none on /sys/fs/cgroup type tmpfs (rw)',
            'none on /sys/fs/fuse/connections type fusectl (rw)',
            'none on /sys/kernel/debug type debugfs (rw)',
            'none on /sys/kernel/security type securityfs (rw)',
            'udev on /dev type devtmpfs (rw,mode=0755)',
            'devpts on /dev/pts type devpts (rw,noexec,nosuid,gid=5,'
            'mode=0620)',
            'tmpfs on /run type tmpfs (rw,noexec,nosuid,size=10%,mode=0755)',
            'none on /run/lock type tmpfs (rw,noexec,nosuid,nodev,'
            'size=5242880)',
            'none on /run/shm type tmpfs (rw,nosuid,nodev)',
            'none on /run/user type tmpfs (rw,noexec,nosuid,nodev,'
            'size=104857600,mode=0755)',
            'none on /sys/fs/pstore type pstore (rw)',
            'cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,relatime,cpuset)',
            'cgroup on /sys/fs/cgroup/cpu type cgroup (rw,relatime,cpu)',
            'cgroup on /sys/fs/cgroup/cpuacct type cgroup (rw,relatime,'
            'cpuacct)',
            'cgroup on /sys/fs/cgroup/memory type cgroup (rw,relatime,memory)',
            'cgroup on /sys/fs/cgroup/devices type cgroup (rw,relatime,'
            'devices)',
            'cgroup on /sys/fs/cgroup/freezer type cgroup (rw,relatime,'
            'freezer)',
            'cgroup on /sys/fs/cgroup/blkio type cgroup (rw,relatime,blkio)',
            'cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,relatime,'
            'perf_event)',
            'cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,relatime,'
            'hugetlb)',
            '/dev/sda1 on /boot type ext2 (rw)',
            'systemd on /sys/fs/cgroup/systemd type cgroup (rw,noexec,nosuid,'
            'nodev,none,name=systemd)',
            '/dev/mapper/vg_prova-lv_prova_vol1 on /home/pippo type ext4 (rw)',
            '']
        mount_point_path = '/home/pippo'
        source = 'mount'

        res = lvm.lvm_guess(mount_point_path, mount_points, source)

        expected_result = ('vg_prova', 'lv_prova_vol1',
                           '/dev/vg_prova/lv_prova_vol1')
        self.assertEqual(res, expected_result)


class Test_validate_lvm_params(unittest.TestCase):
    def setUp(self):
        self.backup_opt = mock.Mock()
        self.backup_opt.lvm_snapperm = 'ro'
        self.backup_opt.path_to_backup = '/path/to/backup'
        self.backup_opt.lvm_srcvol = '/lvm/srcvol'
        self.backup_opt.lvm_volgroup = 'vg_burger'

    def test_return_true_on_lvm_configuration_valid(self):
        self.backup_opt.lvm_srcvol = ''
        self.backup_opt.lvm_volgroup = ''
        self.assertFalse(lvm.validate_lvm_params(self.backup_opt))

    def test_return_false_on_lvm_not_required(self):
        self.assertTrue(lvm.validate_lvm_params(self.backup_opt))

    def test_raises_Exception_on_snapperm_invalid(self):
        self.backup_opt.lvm_snapperm = 'squeezeme'
        self.assertRaises(Exception, lvm.validate_lvm_params,
                          self.backup_opt)  # noqa

    def test_raises_Exception_on_no_pathtobackup(self):
        self.backup_opt.path_to_backup = ''
        self.assertRaises(Exception, lvm.validate_lvm_params,
                          self.backup_opt)  # noqa

    def test_raises_Exception_on_no_lvmsrcvol(self):
        self.backup_opt.lvm_srcvol = ''
        self.assertRaises(Exception, lvm.validate_lvm_params,
                          self.backup_opt)  # noqa

    def test_raises_Exception_on_no_lvmvolgrp(self):
        self.backup_opt.lvm_volgroup = ''
        self.assertRaises(Exception, lvm.validate_lvm_params,
                          self.backup_opt)  # noqa


class Test_umount(unittest.TestCase):
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.os')
    def test_return_none_on_success(self, mock_os, mock_popen):
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        mock_os.rmdir.return_value = None
        self.assertIsNone(lvm._umount('path'))

    @patch('freezer.snapshot.lvm.subprocess.Popen')
    @patch('freezer.snapshot.lvm.os')
    def test_raises_on_popen_returncode_not_0(self, mock_os, mock_popen):
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        mock_os.rmdir.return_value = None
        self.assertRaises(Exception, lvm._umount, 'path')  # noqa


class Test_lvremove(unittest.TestCase):
    @patch('freezer.snapshot.lvm.subprocess.Popen')
    def test_return_none_on_success(self, mock_popen):
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        self.assertIsNone(lvm._lvremove('logicalvolume'))

    @patch('freezer.snapshot.lvm.subprocess.Popen')
    def test_raises_on_popen_returncode_not_0(self, mock_popen):
        mock_process = mock.Mock()
        mock_process.communicate.return_value = '', ''
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        self.assertRaises(Exception, lvm._lvremove, 'path')  # noqa
