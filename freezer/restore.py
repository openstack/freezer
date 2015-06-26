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

Freezer restore modes related functions
"""

import multiprocessing
import os
import logging
import re
import datetime

from freezer.tar import tar_restore
from freezer import swift
from freezer.utils import (validate_all_args, sort_backup_list,
                           date_to_timestamp, ReSizeStream)


def restore_fs(backup_opt_dict):
    """
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
    """

    # List of mandatory values
    required_list = [
        os.path.exists(backup_opt_dict.restore_abs_path),
        backup_opt_dict.container,
        backup_opt_dict.backup_name
    ]

    # Arguments validation. Raise ValueError is all the arguments are not True
    if not validate_all_args(required_list):
        raise ValueError('[*] Error: please provide ALL the following '
                         'arguments: a valid --restore-abs-path '
                         '--container --backup-name')

    if not backup_opt_dict.restore_from_date:
        logging.warning(('[*] Restore date time not available. Setting to '
                         'current datetime'))
        backup_opt_dict.restore_from_date = \
            re.sub(
                r'^(\S+?) (.+?:\d{,2})\.\d+?$', r'\1T\2',
                str(datetime.datetime.now()))

    # If restore_from_host is set to local hostname is not set in
    # backup_opt_dict.restore_from_host
    if backup_opt_dict.restore_from_host:
        backup_opt_dict.hostname = backup_opt_dict.restore_from_host

    # Check if there's a backup matching. If not raise Exception
    remote_obj_list = swift.get_container_content(
        backup_opt_dict.client_manager,
        backup_opt_dict.container)

    backup_opt_dict.remote_match_backup = \
        swift.get_match_backup(backup_opt_dict.backup_name,
                               backup_opt_dict.hostname,
                               remote_obj_list)
    restore_fs_sort_obj(backup_opt_dict)


def restore_fs_sort_obj(backup_opt_dict):
    """
    Take options dict as argument and sort/remove duplicate elements from
    backup_opt_dict.remote_match_backup and find the closes backup to the
    provided from backup_opt_dict.restore_from_date. Once the objects are
    looped backwards and the level 0 backup is found, along with the other
    level 1,2,n, is download the object from swift and untar them locally
    starting from level 0 to level N.
    """

    # Convert backup_opt_dict.restore_from_date to timestamp
    opt_backup_timestamp = date_to_timestamp(backup_opt_dict.restore_from_date)

    # Sort remote backup list using timestamp in reverse order,
    # that is from the newest to the oldest executed backup
    sorted_backups_list = sort_backup_list(backup_opt_dict.remote_match_backup)
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
        raise ValueError('No matching backup name {0} found in '
                         'container {1} for hostname {2}'
                         .format(backup_opt_dict.backup_name,
                                 backup_opt_dict.container,
                                 backup_opt_dict.hostname))

    # Backups are looped from the last element of the list going
    # backwards, as we want to restore starting from the oldest object
    for backup in closest_backup_list[::-1]:
        write_pipe, read_pipe = multiprocessing.Pipe()
        process_stream = multiprocessing.Process(
            target=swift.object_to_stream, args=(
                backup_opt_dict.container, backup_opt_dict.client_manager,
                write_pipe, read_pipe, backup,))
        process_stream.daemon = True
        process_stream.start()

        write_pipe.close()
        # Start the tar pipe consumer process
        tar_stream = multiprocessing.Process(
            target=tar_restore, args=(backup_opt_dict, read_pipe))
        tar_stream.daemon = True
        tar_stream.start()
        read_pipe.close()
        process_stream.join()
        tar_stream.join()

        if tar_stream.exitcode:
            raise Exception('failed to restore file')

    logging.info(
        '[*] Restore execution successfully executed for backup name {0},\
            from container {1}, into directory {2}'.format(
            backup_opt_dict.backup_name, backup_opt_dict.container,
            backup_opt_dict.restore_abs_path))


class RestoreOs:
    def __init__(self, client_manager, container):
        self.client_manager = client_manager
        self.container = container

    def _get_backups(self, path, restore_from_date):
        timestamp = date_to_timestamp(restore_from_date)
        swift = self.client_manager.get_swift()
        info, backups = swift.get_container(self.container, path=path)
        backups = sorted(map(lambda x: int(x["name"].rsplit("/", 1)[-1]),
                             backups))
        backups = filter(lambda x: x >= timestamp, backups)

        if not backups:
            msg = "Cannot find backups for path: %s" % path
            logging.error(msg)
            raise BaseException(msg)
        return backups[-1]

    def _create_image(self, path, restore_from_date):
        swift = self.client_manager.get_swift()
        glance = self.client_manager.get_glance()
        backup = self._get_backups(path, restore_from_date)
        stream = swift.get_object(
            self.container, "%s/%s" % (path, backup), resp_chunk_size=10000000)
        length = int(stream[0]["x-object-meta-length"])
        logging.info("[*] Creation glance image")
        image = glance.images.create(
            data=ReSizeStream(stream[1], length, 1),
            container_format="bare",
            disk_format="raw")
        return stream[0], image

    def restore_cinder(self, restore_from_date, volume_id):
        """
        Restoring cinder backup using
        :param volume_id:
        :return:
        """
        cinder = self.client_manager.get_cinder()
        backups = cinder.backups.findall(volume_id=volume_id,
                                         status='available')
        backups = [x for x in backups if x.created_at >= restore_from_date]
        if not backups:
            logging.error("no available backups for cinder volume")
        else:
            backup = min(backups, key=lambda x: x.created_at)
            cinder.restores.restore(backup_id=backup.id)

    def restore_cinder_by_glance(self, restore_from_date, volume_id):
        """
        1) Define swift directory
        2) Download and upload to glance
        3) Create volume from glance
        4) Delete
        :param restore_from_date - date in format '%Y-%m-%dT%H:%M:%S'
        :param volume_id - id of attached cinder volume
        """
        (info, image) = self._create_image(volume_id, restore_from_date)
        length = int(info["x-object-meta-length"])
        gb = 1073741824
        size = length / gb
        if length % gb > 0:
            size += 1
        logging.info("[*] Creation volume from image")
        self.client_manager.get_cinder().volumes.create(size,
                                                        imageRef=image.id)
        logging.info("[*] Deleting temporary image")
        self.client_manager.get_glance().images.delete(image)

    def restore_nova(self, restore_from_date, instance_id):
        """
        :param restore_from_date:  date in format '%Y-%m-%dT%H:%M:%S'
        :param instance_id: id of attached nova instance
        :return:
        """
        (info, image) = self._create_image(instance_id, restore_from_date)
        nova = self.client_manager.get_nova()
        flavor = nova.flavors.get(info['x-object-meta-tenant-id'])
        logging.info("[*] Creation an instance")
        nova.servers.create(info['x-object-meta-name'], image, flavor)
