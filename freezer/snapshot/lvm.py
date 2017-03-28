"""
(c) Copyright 2014-2016 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Freezer LVM related functions
"""

import os
import re
import subprocess

from oslo_log import log
from oslo_utils import uuidutils

from freezer.common import config as freezer_config
from freezer.utils import utils

LOG = log.getLogger(__name__)


def lvm_snap_remove(backup_opt_dict):
    """
    Unmount the snapshot and removes it

    :param backup_opt_dict.lvm_dirmount: mount point of the snapshot
    :param backup_opt_dict.lvm_volgroup: volume group to which the lv belongs
    :param backup_opt_dict.lvm_snapname: name of the snapshot lv
    :return: None, raises on error
    """
    try:
        _umount(backup_opt_dict.lvm_dirmount)
    except Exception as e:
        LOG.warning("Snapshot unmount errror: {0}".format(e))
    lv = os.path.join('/dev',
                      backup_opt_dict.lvm_volgroup,
                      backup_opt_dict.lvm_snapname)
    _lvremove(lv)
    LOG.info('Snapshot volume {0} removed'.format(lv))


def get_vol_fs_type(vol_name):
    """
    The argument need to be a full path lvm name i.e. /dev/vg0/var
    or a disk partition like /dev/sda1. The returnet value is the
    file system type
    """
    if os.path.exists(vol_name) is False:
        err = 'Provided volume name not found: {0} '.format(vol_name)
        LOG.exception(err)
        raise Exception(err)

    file_cmd = '{0} -0 -bLs --no-pad --no-buffer --preserve-date \
    {1}'.format(utils.find_executable("file"), vol_name)
    file_process = subprocess.Popen(
        file_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=utils.find_executable("bash"))
    (file_out, file_err) = file_process.communicate()
    file_match = re.search(r'(\S+?) filesystem data', file_out, re.I)
    if file_match is None:
        err = 'File system type not guessable: {0}'.format(file_err)
        LOG.exception(err)
        raise Exception(err)
    else:
        filesys_type = file_match.group(1)
        LOG.info('File system {0} found for volume {1}'.format(
            filesys_type, vol_name))
        return filesys_type.lower().strip()


def lvm_snap(backup_opt_dict):
    """
    Checks the provided parameters and create the lvm snapshot if requested

    The path_to_backup might be adjusted in case the user requested
    a lvm snapshot without specifying an exact path for the snapshot).
    The assumption in this case is that the user wants to use the lvm snapshot
    capability to backup the specified filesystem path, leaving out all
    the rest of the parameters which will guessed and set by freezer.

    :param backup_opt_dict: the configuration dict
    :return: True if the snapshot has been taken, False otherwise
    """
    lvm_uuid = uuidutils.generate_uuid(dashed=False)

    if not backup_opt_dict.lvm_snapname:
        backup_opt_dict.lvm_snapname = \
            "{0}_{1}".format(freezer_config.DEFAULT_LVM_SNAP_BASENAME,
                             lvm_uuid)

    # adjust/check lvm parameters according to provided path_to_backup
    lvm_info = get_lvm_info(backup_opt_dict.path_to_backup)

    if not backup_opt_dict.lvm_volgroup:
        backup_opt_dict.lvm_volgroup = lvm_info['volgroup']

    if not backup_opt_dict.lvm_srcvol:
        backup_opt_dict.lvm_srcvol = lvm_info['srcvol']

    if not backup_opt_dict.lvm_dirmount:
        utils.create_dir(freezer_config.DEFAULT_LVM_MOUNT_BASEDIR)
        backup_opt_dict.lvm_dirmount = \
            "{0}/mount_{1}".format(freezer_config.DEFAULT_LVM_MOUNT_BASEDIR,
                                   lvm_uuid)

    backup_opt_dict.path_to_backup = os.path.join(backup_opt_dict.lvm_dirmount,
                                                  lvm_info['snap_path'])

    if not validate_lvm_params(backup_opt_dict):
        LOG.info('No LVM requested/configured')
        return False

    utils.create_dir(backup_opt_dict.lvm_dirmount)

    if '%' in backup_opt_dict.lvm_snapsize:
        lvm_size_option = "--extents"
    else:
        lvm_size_option = "--size"

    lvm_create_command = (
        '{0} {1} {2} --snapshot --permission {3} '
        '--name {4} {5}'.format(
            utils.find_executable('lvcreate'),
            lvm_size_option,
            backup_opt_dict.lvm_snapsize,
            ('r' if backup_opt_dict.lvm_snapperm == 'ro'
             else backup_opt_dict.lvm_snapperm),
            backup_opt_dict.lvm_snapname,
            backup_opt_dict.lvm_srcvol))

    lvm_process = subprocess.Popen(
        lvm_create_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=utils.find_executable('bash'))
    (lvm_out, lvm_err) = lvm_process.communicate()

    if lvm_process.returncode:
        raise Exception('lvm snapshot creation error: {0}'.format(lvm_err))

    LOG.debug('{0}'.format(lvm_out))
    LOG.warning('Logical volume "{0}" created'.
                format(backup_opt_dict.lvm_snapname))

    # Guess the file system of the provided source volume and st mount
    # options accordingly
    filesys_type = get_vol_fs_type(backup_opt_dict.lvm_srcvol)
    mount_options = '-o {}'.format(backup_opt_dict.lvm_snapperm)
    if 'xfs' == filesys_type:
        mount_options = ' -onouuid '
    # Mount the newly created snapshot to dir_mount
    abs_snap_name = '/dev/{0}/{1}'.format(
        backup_opt_dict.lvm_volgroup,
        backup_opt_dict.lvm_snapname)
    mount_command = '{0} {1} {2} {3}'.format(
        utils.find_executable('mount'),
        mount_options,
        abs_snap_name,
        backup_opt_dict.lvm_dirmount)
    mount_process = subprocess.Popen(
        mount_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=utils.find_executable('bash'))
    mount_err = mount_process.communicate()[1]
    if 'already mounted' in mount_err:
        LOG.warning('Volume {0} already mounted on {1}\
        '.format(abs_snap_name, backup_opt_dict.lvm_dirmount))
        return True
    if mount_err:
        LOG.error("Snapshot mount error. Removing snapshot")
        lvm_snap_remove(backup_opt_dict)
        raise Exception('lvm snapshot mounting error: {0}'.format(mount_err))
    else:
        LOG.warning(
            'Volume {0} successfully mounted on {1}'.format(
                abs_snap_name, backup_opt_dict.lvm_dirmount))

    return True


def get_lvm_info(path):
    """
    Take a file system path as argument as backup_opt_dict.path_to_backup
    and return a list containing lvm_srcvol, lvm_volgroup
    where the path is mounted on.

    :param path: the original file system path where backup needs
    to be executed
    :returns: a dict containing the keys 'volgroup', 'srcvol' and 'snap_path'
    """

    mount_point_path, snap_path = utils.get_mount_from_path(path)

    with open('/proc/mounts', 'r') as mount_fd:
        mount_points = mount_fd.readlines()
        lvm_volgroup, lvm_srcvol, lvm_device = lvm_guess(
            mount_point_path, mount_points, '/proc/mounts')

    if not lvm_device:
        mount_process = subprocess.Popen(
            ['mount'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=os.environ)
        mount_out, mount_err = mount_process.communicate()
        mount_points = mount_out.split('\n')
        lvm_volgroup, lvm_srcvol, lvm_device = lvm_guess(
            mount_point_path, mount_points, 'mount')

    if not lvm_device:
        raise Exception(
            'Cannot find {0} in {1}, please provide volume group and '
            'volume name explicitly'.format(mount_point_path, mount_points))

    lvm_params = {'volgroup': lvm_volgroup,
                  'srcvol': lvm_device,
                  'snap_path': snap_path}

    return lvm_params


def lvm_guess(mount_point_path, mount_points, source='/proc/mounts'):
    """Guess lvm vol group and vol name from mount point

    Extract the vol group and vol name from given list
    of mount_points and mount_point_path

    :param mount_point_path: mount path
    :param mount_points: list of currently mounted devices
    :return: a list containing volume group, volume name and full device path
    """

    lvm_volgroup = lvm_srcvol = lvm_device = None
    for mount_line in mount_points:
        if source == '/proc/mounts':
            device, mount_path = mount_line.split(' ')[0:2]
        elif source == 'mount':
            mount_list = mount_line.split(' ')[0:3]
            device = mount_list[0]
            mount_path = mount_list[2]
        if mount_point_path.strip() == mount_path.strip():
            mount_match = re.search(
                r'/dev/mapper/(\w.+?\w)-(\w.+?\w)$', device)
            if mount_match:
                lvm_volgroup = mount_match.group(1).replace('--', '-')
                lvm_srcvol = mount_match.group(2).replace('--', '-')
                lvm_device = u'/dev/{0}/{1}'.format(lvm_volgroup, lvm_srcvol)
                break

    return lvm_volgroup, lvm_srcvol, lvm_device


def validate_lvm_params(backup_opt_dict):
    """
    Validates the parameters and raises in case of missing values

    :param backup_opt_dict:
    :return: False is snapshot is not requested,
             True snapshot is requested and parameters are valid
    """
    if backup_opt_dict.lvm_snapperm not in ('ro', 'rw'):
        raise ValueError('Error: Invalid value for option lvm-snap-perm: '
                         '{}'.format(backup_opt_dict.lvm_snapperm))

    if not backup_opt_dict.path_to_backup:
        raise ValueError('Error: no path-to-backup and '
                         'no lvm-auto-snap provided')

    if not backup_opt_dict.lvm_srcvol and not backup_opt_dict.lvm_volgroup:
        # no lvm parameters provided, assume lvm snapshot is not requested
        return False

    if not backup_opt_dict.lvm_srcvol:
        raise ValueError('Error: no lvm-srcvol and '
                         'no lvm-auto-snap provided')
    if not backup_opt_dict.lvm_volgroup:
        raise ValueError('Error: no lvm-volgroup and '
                         'no lvm-auto-snap provided')

    LOG.info('Source LVM Volume: {0}'.format(
        backup_opt_dict.lvm_srcvol))
    LOG.info('LVM Volume Group: {0}'.format(
        backup_opt_dict.lvm_volgroup))
    LOG.info('Snapshot name: {0}'.format(
        backup_opt_dict.lvm_snapname))
    LOG.info('Snapshot size: {0}'.format(
        backup_opt_dict.lvm_snapsize))
    LOG.info('Directory where the lvm snaphost will be mounted on:'
             ' {0}'.format(backup_opt_dict.lvm_dirmount.strip()))
    LOG.info('Path to backup (including snapshot): {0}'
             .format(backup_opt_dict.path_to_backup))

    return True


def _umount(path):
    if os.getcwd().startswith(path):
        os.chdir('/')
    umount_proc = subprocess.Popen('{0} -l -f {1}'.format(
        utils.find_executable('umount'), path),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True, executable=utils.find_executable('bash'))
    (umount_out, mount_err) = umount_proc.communicate()

    if umount_proc.returncode:
        raise Exception('Impossible to umount {0}. {1}'
                        .format(path, mount_err))
    os.rmdir(path)
    LOG.info('Volume {0} unmounted'.format(path))


def _lvremove(lv):
    for attempt in range(5):
        lvremove_proc = subprocess.Popen(
            '{0} -f {1}'.format(utils.find_executable('lvremove'), lv),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True,
            executable=utils.find_executable('bash'))
        output, error = lvremove_proc.communicate()
        if lvremove_proc.returncode:
            if "contains a filesystem in use" in error:
                LOG.warning("Couldn't remove volume {0}. "
                            "It is still in use.".format(lv))
                log_volume_holding_process(lv)
            else:
                break
        else:
            return
    # Raise if five attempts made or different error than fs in use
    raise Exception('Unable to remove snapshot {0}. {1}'.format(lv, error))


def log_volume_holding_process(lv):
    try:
        # Let's try to provide more information on the failure
        devices = [i.split("\t") for i in subprocess.check_output([
            utils.find_executable('dmsetup'), "ls"]).splitlines()]
        dev_id = [i[1].strip("()").split(":") for i in devices if
                  lv.split("/").pop() in i[0] and
                  not i[0].endswith("cow")][0]
        command = "{} | grep {},{}".format(
            # lsof is quite long, so no need to add a sleep here
            utils.find_executable('lsof'), dev_id[0], dev_id[1])
        process = subprocess.check_output([command], shell=True)
        LOG.warning("Process holding the volume is '{}'".format(process))
    except Exception as e:
        LOG.warning("Could not get informations on the process holding the"
                    " volume: {}".format(str(e)))
