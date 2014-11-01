'''
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

Freezer restore modes related functions
'''

from freezer.tar import tar_restore
from freezer.swift import object_to_stream
from freezer.utils import (
    validate_all_args, get_match_backup, sort_backup_list)

from multiprocessing import Process, Pipe
import os
import logging
import re
import datetime
import time


def restore_fs(backup_opt_dict):
    '''
    Restore data from swift server to your local node. Data will be restored
    in the directory specified in backup_opt_dict.restore_abs_path. The
    object specified with the --get-object option will be downloaded from
    the Swift server and will be downloaded inside the parent directory of
    backup_opt_dict.restore_abs_path. If the object was compressed during
    backup time, then it is decrypted, decompressed and de-archived to
    backup_opt_dict.restore_abs_path. Before download the file, the size of
    the local volume/disk/partition will be computed. If there is enough space
    the full restore will be executed. Please remember to stop any service
    that require access to the data before to start the restore execution
    and to start the service at the end of the restore execution
    '''

    # List of mandatory values
    required_list = [
        os.path.exists(backup_opt_dict.restore_abs_path),
        backup_opt_dict.remote_obj_list,
        backup_opt_dict.container,
        backup_opt_dict.backup_name
        ]

    # Arugment validation. Raise ValueError is all the arguments are not True
    if not validate_all_args(required_list):
        logging.critical("[*] Error: please provide ALL the following \
            arguments: {0}".format(' '.join(required_list)))
        raise ValueError

    if not backup_opt_dict.restore_from_date:
        logging.warning('[*] Restore date time not available. Setting to \
            current datetime')
        backup_opt_dict.restore_from_date = \
            re.sub(
                r'^(\S+?) (.+?:\d{,2})\.\d+?$', r'\1T\2',
                str(datetime.datetime.now()))

    # If restore_from_host is set to local hostname is not set in
    # backup_opt_dict.restore_from_host
    if backup_opt_dict.restore_from_host:
        backup_opt_dict.hostname = backup_opt_dict.restore_from_host

    # Check if there's a backup matching. If not raise Exception
    backup_opt_dict = get_match_backup(backup_opt_dict)
    if not backup_opt_dict.remote_match_backup:
        logging.critical(
            '[*] Not backup found matching with name: {0},\
                hostname: {1}'.format(
                backup_opt_dict.backup_name, backup_opt_dict.hostname))
        raise ValueError

    restore_fs_sort_obj(backup_opt_dict)


def restore_fs_sort_obj(backup_opt_dict):
    '''
    Take options dict as argument and sort/remove duplicate elements from
    backup_opt_dict.remote_match_backup and find the closes backup to the
    provided from backup_opt_dict.restore_from_date. Once the objects are
    looped backwards and the level 0 backup is found, along with the other
    level 1,2,n, is download the object from swift and untar them locally
    starting from level 0 to level N.
    '''

    # Convert backup_opt_dict.restore_from_date to timestamp
    fmt = '%Y-%m-%dT%H:%M:%S'
    opt_backup_date = datetime.datetime.strptime(
        backup_opt_dict.restore_from_date, fmt)
    opt_backup_timestamp = int(time.mktime(opt_backup_date .timetuple()))

    # Sort remote backup list using timestamp in reverse order,
    # that is from the newest to the oldest executed backup
    sorted_backups_list = sort_backup_list(backup_opt_dict)
    # Get the closest earlier backup to date set in
    # backup_opt_dict.restore_from_date
    closest_backup_list = []
    for backup_obj in sorted_backups_list:
        if backup_obj.startswith('tar_metadata'):
            continue
        obj_name_match = re.search(
            r'\S+?_{0}_(\d+)_(\d+?)$'.format(backup_opt_dict.backup_name),
            backup_obj, re.I)
        if not obj_name_match:
            continue
        # Ensure provided timestamp is bigger then object timestamp
        if opt_backup_timestamp >= int(obj_name_match.group(1)):
            closest_backup_list.append(backup_obj)
            # If level 0 is reached, break the loop as level 0 is the first
            # backup we want to restore
            if int(obj_name_match.group(2)) == 0:
                break

    if not closest_backup_list:
        logging.info('[*] No matching backup name {0} found in \
            container {1} for hostname {2}'.format(
            backup_opt_dict.backup_name, backup_opt_dict.container,
            backup_opt_dict.hostname))
        raise ValueError

    # Backups are looped from the last element of the list going
    # backwards, as we want to restore starting from the oldest object
    for backup in closest_backup_list[::-1]:
        write_pipe, read_pipe = Pipe()
        process_stream = Process(
            target=object_to_stream, args=(
                backup_opt_dict, write_pipe, read_pipe, backup,))
        process_stream.daemon = True
        process_stream.start()

        write_pipe.close()
        # Start the tar pipe consumer process
        tar_stream = Process(
            target=tar_restore, args=(backup_opt_dict, read_pipe))
        tar_stream.daemon = True
        tar_stream.start()
        read_pipe.close()
        process_stream.join()
        tar_stream.join()

    logging.info(
        '[*] Restore execution successfully executed for backup name {0},\
            from container {1}, into directory {2}'.format(
            backup_opt_dict.backup_name, backup_opt_dict.container,
            backup_opt_dict.restore_abs_path))
