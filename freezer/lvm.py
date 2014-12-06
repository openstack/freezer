"""
Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

Freezer LVM related functions
"""

from freezer.utils import (
    create_dir, get_vol_fs_type, validate_all_args, get_mount_from_path)

import re
import os
import subprocess
import logging


def lvm_eval(backup_opt_dict):
    """
    Evaluate if the backup must be executed using lvm snapshot
    or just directly on the plain filesystem. If no lvm options are specified
    the backup will be executed directly on the file system and without
    use lvm snapshot. If one of the lvm options are set, then the lvm snap
    will be used to execute backup. This mean all the required options
    must be set accordingly
    """

    required_list = [
        backup_opt_dict.lvm_volgroup,
        backup_opt_dict.lvm_srcvol,
        backup_opt_dict.lvm_dirmount]

    if not validate_all_args(required_list):
        logging.warning('[*] Required lvm options not set. The backup will \
            execute without lvm snapshot.')
        return False

    # Create lvm_dirmount dir if it doesn't exists and write action in logs
    create_dir(backup_opt_dict.lvm_dirmount)

    return True


def lvm_snap_remove(backup_opt_dict):
    """
    Remove the specified lvm_snapshot. If the volume is mounted
    it will unmount it and then removed
    """

    if not lvm_eval(backup_opt_dict):
        return True

    vol_group = backup_opt_dict.lvm_volgroup.replace('-', '--')
    snap_name = backup_opt_dict.lvm_snapname.replace('-', '--')
    mapper_snap_vol = '/dev/mapper/{0}-{1}'.format(vol_group, snap_name)
    proc_mount_fd = open('/proc/mounts', 'r')
    for mount_line in proc_mount_fd:
        if mapper_snap_vol.lower() in mount_line.lower():
            mount_list = mount_line.split(' ')
            (dev_vol, mount_point) = mount_list[0], mount_list[1]
            logging.warning('[*] Found lvm snapshot {0} mounted on {1}\
            '.format(dev_vol, mount_point))
            umount_proc = subprocess.Popen('{0} -l -f {1}'.format(
                backup_opt_dict.umount_path, mount_point),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, executable=backup_opt_dict.bash_path)
            (umount_out, mount_err) = umount_proc.communicate()
            if re.search(r'\S+', umount_out):
                err = '[*] Error: impossible to umount {0} {1}'.format(
                    mount_point, mount_err)
                logging.critical(err)
                raise Exception(err)
            else:
                # Change working directory to be able to unmount
                os.chdir(backup_opt_dict.workdir)
                logging.info('[*] Volume {0} unmounted'.format(
                    mapper_snap_vol))
                snap_rm_proc = subprocess.Popen(
                    '{0} -f {1}'.format(
                        backup_opt_dict.lvremove_path, mapper_snap_vol),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    shell=True, executable=backup_opt_dict.bash_path)
                (lvm_rm_out, lvm_rm_err) = snap_rm_proc.communicate()
                if 'successfully removed' in lvm_rm_out:
                    logging.info('[*] {0}'.format(lvm_rm_out))
                    return True
                else:
                    err = '[*] Error: lvm_snap_rm {0}'.format(lvm_rm_err)
                    logging.critical(err)
                    raise Exception(err)
    raise Exception('[*] Error: no lvm snap removed')


def lvm_snap(backup_opt_dict):
    """
    Implement checks on lvm volumes availability. According to these checks
    we might create an lvm snapshot and mount it or use an existing one
    """

    if lvm_eval(backup_opt_dict) is not True:
        return True
    # Setting lvm snapsize to 5G is not set
    if backup_opt_dict.lvm_snapsize is False:
        backup_opt_dict.lvm_snapsize = '5G'
        logging.warning('[*] lvm_snapsize not configured. Setting the \
        lvm snapshot size to 5G')

    # Setting lvm snapshot name to freezer_backup_snap it not set
    if backup_opt_dict.lvm_snapname is False:
        backup_opt_dict.lvm_snapname = 'freezer_backup_snap'
        logging.warning('[*] lvm_snapname not configured. Setting default \
        name "freezer_backup_snap" for the lvm backup snap session')

    logging.info('[*] Source LVM Volume: {0}'.format(
        backup_opt_dict.lvm_srcvol))
    logging.info('[*] LVM Volume Group: {0}'.format(
        backup_opt_dict.lvm_volgroup))
    logging.info('[*] Snapshot name: {0}'.format(
        backup_opt_dict.lvm_snapname))
    logging.info('[*] Snapshot size: {0}'.format(
        backup_opt_dict.lvm_snapsize))
    logging.info('[*] Directory where the lvm snaphost will be mounted on:\
        {0}'.format(backup_opt_dict.lvm_dirmount.strip()))

    # Create the snapshot according the values passed from command line
    lvm_create_snap = '{0} --size {1} --snapshot --name {2} {3}\
    '.format(
        backup_opt_dict.lvcreate_path,
        backup_opt_dict.lvm_snapsize,
        backup_opt_dict.lvm_snapname,
        backup_opt_dict.lvm_srcvol)

    # If backup mode is mysql, then the db will be flushed and read locked
    # before the creation of the lvm snap
    if backup_opt_dict.mode == 'mysql':
        cursor = backup_opt_dict.mysql_db_inst.cursor()
        cursor.execute('FLUSH TABLES WITH READ LOCK')
        backup_opt_dict.mysql_db_inst.commit()

    lvm_process = subprocess.Popen(
        lvm_create_snap, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=backup_opt_dict.bash_path)
    (lvm_out, lvm_err) = lvm_process.communicate()
    if lvm_err is False:
        err = '[*] lvm snapshot creation error: {0}'.format(lvm_err)
        logging.critical(err)
        raise Exception(err)
    else:
        logging.warning('[*] {0}'.format(lvm_out))

    # Unlock MySQL Tables if backup is == mysql
    if backup_opt_dict.mode == 'mysql':
        cursor.execute('UNLOCK TABLES')
        backup_opt_dict.mysql_db_inst.commit()
        cursor.close()
        backup_opt_dict.mysql_db_inst.close()

    # Guess the file system of the provided source volume and st mount
    # options accordingly
    filesys_type = get_vol_fs_type(backup_opt_dict)
    mount_options = ' '
    if 'xfs' == filesys_type:
        mount_options = ' -onouuid '
    # Mount the newly created snapshot to dir_mount
    abs_snap_name = '/dev/{0}/{1}'.format(
        backup_opt_dict.lvm_volgroup,
        backup_opt_dict.lvm_snapname)
    mount_snap = '{0} {1} {2} {3}'.format(
        backup_opt_dict.mount_path,
        mount_options,
        abs_snap_name,
        backup_opt_dict.lvm_dirmount)
    mount_process = subprocess.Popen(
        mount_snap, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=backup_opt_dict.bash_path)
    mount_err = mount_process.communicate()[1]
    if 'already mounted' in mount_err:
        logging.warning('[*] Volume {0} already mounted on {1}\
        '.format(abs_snap_name, backup_opt_dict.lvm_dirmount))
        return True
    if mount_err:
        err = '[*] lvm snapshot mounting error: {0}'.format(mount_err)
        logging.critical(err)
        raise Exception(err)
    else:
        logging.warning(
            '[*] Volume {0} succesfully mounted on {1}'.format(
                abs_snap_name, backup_opt_dict.lvm_dirmount))
    return True


def get_lvm_info(backup_opt_dict):
    """
    Take a file system path as argument as backup_opt_dict.src_file
    and return a dictionary containing dictionary['lvm_srcvol']
    and dictionary['lvm_volgroup'] where the path is mounted on.

    :param backup_opt_dict: backup_opt_dict.src_file, the file system path
    :returns: the dictionary backup_opt_dict containing keys lvm_srcvol
              and lvm_volgroup with respective values
    """

    mount_point_path = get_mount_from_path(backup_opt_dict.lvm_auto_snap)
    with open('/proc/mounts', 'r') as mount_fd:
        mount_points = mount_fd.readlines()

    for mount_line in mount_points:
        device, mount_path = mount_line.split(' ')[0:2]
        if mount_point_path.strip() == mount_path.strip():
            mount_match = re.search(
                r'/dev/mapper/(\w.+?\w)-(\w.+?\w)$', device)
            if mount_match:
                backup_opt_dict.__dict__['lvm_volgroup'] = \
                    mount_match.group(1).replace('--', '-')
                lvm_srcvol = mount_match.group(2).replace('--', '-')
                backup_opt_dict.__dict__['lvm_srcvol'] = \
                    u'/dev/{0}/{1}'.format(
                    backup_opt_dict.lvm_volgroup, lvm_srcvol)
                break

    return backup_opt_dict
