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

Freezer functions to interact with OpenStack Swift client and server
"""
from freezer.storages.swiftstorage import SwiftStorage

from freezer.utils import (sort_backup_list, DateTime, segments_name)
import json
import re
import time
import logging

RESP_CHUNK_SIZE = 65536


def show_containers(containers_list):
    """
    Print remote containers in sorted order
    """

    ordered_container = {}
    for container in containers_list:
        ordered_container['container_name'] = container['name']
        size = '{0}'.format((int(container['bytes']) / 1024) / 1024)
        if size == '0':
            size = '1'
        ordered_container['size'] = '{0}MB'.format(size)
        ordered_container['objects_count'] = container['count']
        print json.dumps(
            ordered_container, indent=4,
            separators=(',', ': '), sort_keys=True)


def show_objects(backup_opt_dict):
    """
    Retreive the list of backups from backup_opt_dict for the specified \
    container and print them nicely to std out.
    """

    if not backup_opt_dict.list_objects:
        return False

    ordered_objects = {}
    remote_obj = get_container_content(
        backup_opt_dict.client_manager,
        backup_opt_dict.container)

    for obj in remote_obj:
        ordered_objects['object_name'] = obj['name']
        ordered_objects['upload_date'] = obj['last_modified']
        print json.dumps(
            ordered_objects, indent=4,
            separators=(',', ': '), sort_keys=True)

    return True


def _remove_object(sw_connector, container, obj):
    logging.info('[*] Removing backup object: {0}'.format(obj))
    sleep_time = 120
    retry_max_count = 60
    curr_count = 0
    while True:
        try:
            sw_connector.delete_object(container, obj)
            logging.info(
                '[*] Remote object {0} removed'.format(obj))
            break
        except Exception as error:
            curr_count += 1
            time.sleep(sleep_time)
            err_msg = (
                '[*] Remote Object {0} failed to be removed.'
                ' Retrying intent {1} out of {2} totals'.format(
                    obj, curr_count, retry_max_count))
            if curr_count >= retry_max_count:
                error_message = \
                    '[*] Error: {0}: {1}'.format(err_msg, error)
                raise Exception(error_message)
            else:
                logging.warning(err_msg)


def remove_object(sw_connector, container, obj):
    head_info = sw_connector.head_object(container, obj)
    manifest = head_info.get('x-object-manifest', None)
    _remove_object(sw_connector, container, obj)
    if not manifest:
        return
    segments_container, segments_match = manifest.split('/')
    logging.info("Removing segments of object {0} from container {1}".
                 format(obj, segments_container))
    segment_list = sw_connector.get_container(segments_container)[1]
    for segment in segment_list:
        if segment['name'].startswith(segments_match):
            _remove_object(sw_connector, segments_container, segment['name'])


def remove_obj_older_than(backup_opt_dict):
    """
    Remove object in remote swift server which are
    older than the specified days or timestamp
    """

    remote_obj_list = get_container_content(
        backup_opt_dict.client_manager,
        backup_opt_dict.container)

    if not remote_obj_list:
        logging.warning('[*] No remote objects will be removed')
        return

    if backup_opt_dict.remove_older_than is not None:
        if backup_opt_dict.remove_from_date:
            raise Exception("Please specify remove date unambiguously")
        current_timestamp = backup_opt_dict.time_stamp
        max_age = int(backup_opt_dict.remove_older_than * 86400)
        remove_from = DateTime(current_timestamp - max_age)
    else:
        if not backup_opt_dict.remove_from_date:
            raise Exception("Remove date/age not specified")
        remove_from = DateTime(backup_opt_dict.remove_from_date)

    logging.info('[*] Removing objects older than {0} ({1})'.format(
        remove_from, remove_from.timestamp))

    backup_name = backup_opt_dict.backup_name
    hostname = backup_opt_dict.hostname
    backup_opt_dict.remote_match_backup = \
        get_match_backup(backup_opt_dict.backup_name,
                         backup_opt_dict.hostname,
                         remote_obj_list)
    sorted_remote_list = sort_backup_list(backup_opt_dict.remote_match_backup)

    tar_meta_incremental_dep_flag = False
    incremental_dep_flag = False

    for match_object in sorted_remote_list:
        obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
            hostname, backup_name), match_object, re.I)

        if obj_name_match:
            remote_obj_timestamp = int(obj_name_match.group(2))

            if remote_obj_timestamp >= remove_from.timestamp:
                if match_object.startswith('tar_meta'):
                    tar_meta_incremental_dep_flag = \
                        (obj_name_match.group(3) != '0')
                else:
                    incremental_dep_flag = \
                        (obj_name_match.group(3) != '0')

            else:
                sw_connector = backup_opt_dict.client_manager.get_swift()
                if match_object.startswith('tar_meta'):
                    if not tar_meta_incremental_dep_flag:
                        remove_object(sw_connector,
                                      backup_opt_dict.container, match_object)
                    else:
                        if obj_name_match.group(3) == '0':
                            tar_meta_incremental_dep_flag = False
                else:
                    if not incremental_dep_flag:
                        remove_object(sw_connector,
                                      backup_opt_dict.container, match_object)
                    else:
                        if obj_name_match.group(3) == '0':
                            incremental_dep_flag = False


def get_container_content(client_manager, container):
    """
    Download the list of object of the provided container
    and print them out as container meta-data and container object list
    """

    sw_connector = client_manager.get_swift()
    try:
        return sw_connector.get_container(container)[1]
    except Exception as error:
        raise Exception('[*] Error: get_object_list: {0}'.format(error))


def add_stream(client_manager, container, stream,
               package_name, headers=None):
    i = 0
    container_segments = segments_name(container)
    swift_storage = SwiftStorage(client_manager, container)

    for el in stream:
        swift_storage.upload_chunk("{0}/{1}".format(package_name, "%08d" % i),
                                   el)
        i += 1
    if not headers:
        headers = {}
    headers['X-Object-Manifest'] = u'{0}/{1}/'.format(
        container_segments, package_name)
    headers['x-object-meta-length'] = len(stream)

    swift = client_manager.get_swift()
    swift.put_object(container, package_name, "", headers=headers)


def object_to_stream(container, client_manager, write_pipe, read_pipe,
                     obj_name):
    """
    Take a payload downloaded from Swift
    and generate a stream to be consumed from other processes
    """
    sw_connector = client_manager.get_swift()
    logging.info('[*] Downloading data stream...')

    # Close the read pipe in this child as it is unneeded
    # and download the objects from swift in chunks. The
    # Chunk size is set by RESP_CHUNK_SIZE and sent to che write
    # pipe
    read_pipe.close()
    for obj_chunk in sw_connector.get_object(
            container, obj_name, resp_chunk_size=RESP_CHUNK_SIZE)[1]:
        write_pipe.send_bytes(obj_chunk)

    # Closing the pipe after checking no data
    # is still available in the pipe.
    while True:
        if not write_pipe.poll():
            write_pipe.close()
            break
        time.sleep(1)


def get_match_backup(backup_name, hostname, remote_obj_list):
    """
    Return a dictionary containing a list of remote matching backups from
    backup_opt_dict.remote_obj_list.
    Backup have to exactly match against backup name and hostname of the
    node where freezer is executed. The matching objects are stored and
    available in backup_opt_dict.remote_match_backup
    """

    backup_name = backup_name.lower()
    remote_match_backup = []

    for container_object in remote_obj_list:
        object_name = container_object.get('name', None)
        if object_name:
            obj_name_match = re.search(r'{0}_({1})_\d+?_\d+?$'.format(
                hostname, backup_name), object_name.lower(), re.I)
            if obj_name_match:
                remote_match_backup.append(object_name)

    return remote_match_backup


def get_rel_oldest_backup(hostname, backup_name, remote_obj_list):
    """
    Return from swift, the relative oldest backup matching the provided
    backup name and hostname of the node where freezer is executed.
    The relative oldest backup correspond the oldest backup from the
    last level 0 backup.
    """
    first_backup_name = ''
    first_backup_ts = 0
    for container_object in remote_obj_list:
        object_name = container_object.get('name', None)
        if not object_name:
            continue
        obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
            hostname, backup_name), object_name, re.I)
        if not obj_name_match:
            continue
        remote_obj_timestamp = int(obj_name_match.group(2))
        remote_obj_level = int(obj_name_match.group(3))
        if remote_obj_level == 0 and (remote_obj_timestamp > first_backup_ts):
            first_backup_name = object_name
            first_backup_ts = remote_obj_timestamp

    return first_backup_name


def eval_restart_backup(backup_opt_dict):
    """
    Restart backup level if the first backup execute with always_level
    is older then restart_always_level
    """

    if not backup_opt_dict.restart_always_level:
        logging.info('[*] No need to set Backup {0} to level 0.'.format(
            backup_opt_dict.backup_name))
        return False

    logging.info('[*] Checking always backup level timestamp...')
    # Compute the amount of seconds to be compared with
    # the remote backup timestamp
    max_time = int(float(backup_opt_dict.restart_always_level) * 86400)
    current_timestamp = backup_opt_dict.time_stamp
    backup_name = backup_opt_dict.backup_name
    hostname = backup_opt_dict.hostname
    # Get relative oldest backup by calling get_rel_oldes_backup()

    remote_obj_list = get_container_content(
        backup_opt_dict.client_manager,
        backup_opt_dict.container)
    backup_opt_dict.remote_rel_oldest =\
        get_rel_oldest_backup(hostname, backup_name, remote_obj_list)
    if not backup_opt_dict.remote_rel_oldest:
        logging.info('[*] Relative oldest backup for backup name {0} on \
            host {1} not available. The backup level is NOT restarted'.format(
            backup_name, hostname))
        return False

    obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
        hostname, backup_name), backup_opt_dict.remote_rel_oldest, re.I)
    if not obj_name_match:
        err = ('[*] No backup match available for backup {0} '
               'and host {1}'.format(backup_name, hostname))
        logging.info(err)
        return Exception(err)

    first_backup_ts = int(obj_name_match.group(2))
    if (current_timestamp - first_backup_ts) > max_time:
        logging.info(
            '[*] Backup {0} older then {1} days. Backup level set to 0'.format(
                backup_name, backup_opt_dict.restart_always_level))

        return True
    else:
        logging.info('[*] No need to set level 0 for Backup {0}.'.format(
            backup_name))

    return False


def set_backup_level(backup_opt_dict, manifest_meta_dict):
    """
    Set the backup level params in backup_opt_dict and the swift
    manifest. This is a fundamental part of the incremental backup
    """

    if manifest_meta_dict.get('x-object-meta-backup-name'):
        backup_opt_dict.curr_backup_level = int(
            manifest_meta_dict.get('x-object-meta-backup-current-level'))
        max_level = manifest_meta_dict.get(
            'x-object-meta-maximum-backup-level')
        always_level = manifest_meta_dict.get(
            'x-object-meta-always-backup-level')
        restart_always_level = manifest_meta_dict.get(
            'x-object-meta-restart-always-backup')
        if max_level:
            max_level = int(max_level)
            if backup_opt_dict.curr_backup_level < max_level:
                backup_opt_dict.curr_backup_level += 1
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    str(backup_opt_dict.curr_backup_level)
            else:
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    backup_opt_dict.curr_backup_level = '0'
        elif always_level:
            always_level = int(always_level)
            if backup_opt_dict.curr_backup_level < always_level:
                backup_opt_dict.curr_backup_level += 1
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    str(backup_opt_dict.curr_backup_level)
            # If restart_always_level is set, the backup_age will be computed
            # and if the backup age in days is >= restart_always_level, then
            # backup-current-level will be set to 0
            if restart_always_level:
                backup_opt_dict.restart_always_level = restart_always_level
                if eval_restart_backup(backup_opt_dict):
                    backup_opt_dict.curr_backup_level = '0'
                    manifest_meta_dict['x-object-meta-backup-current-level'] \
                        = '0'
    else:
        backup_opt_dict.curr_backup_level = \
            manifest_meta_dict['x-object-meta-backup-current-level'] = '0'

    return backup_opt_dict, manifest_meta_dict


def check_backup_and_tar_meta_existence(backup_opt_dict):
    """
    Check if any backup is already available on Swift.
    The verification is done by backup_name, which needs to be unique
    in Swift. This function will return an empty dict if no backup are
    found or the Manifest metadata if the backup_name is available
    """

    if not backup_opt_dict.backup_name or not backup_opt_dict.container:
        logging.warning(
            ('[*] A valid Swift container, or backup name or container '
             'content not available. Level 0 backup is being executed '))
        return dict()

    logging.info("[*] Retrieving backup name {0} on container \
    {1}".format(
        backup_opt_dict.backup_name.lower(), backup_opt_dict.container))

    remote_obj_list = get_container_content(
        backup_opt_dict.client_manager,
        backup_opt_dict.container)
    remote_match_backup = \
        get_match_backup(backup_opt_dict.backup_name,
                         backup_opt_dict.hostname,
                         remote_obj_list)
    try:
        remote_newest_backup = get_newest_backup(backup_opt_dict.hostname,
                                                 backup_opt_dict.backup_name,
                                                 remote_match_backup)
        swift = backup_opt_dict.client_manager.get_swift()
        logging.info("[*] Backup {0} found!".format(
            backup_opt_dict.backup_name))
        backup_match = swift.head_object(
            backup_opt_dict.container, remote_newest_backup)

        return backup_match
    except Exception:
        logging.warning("[*] No such backup {0} available... Executing \
            level 0 backup".format(backup_opt_dict.backup_name))
        return dict()


def get_newest_backup(hostname, backup_name, remote_match_backup):
    """
    Return from backup_opt_dict.remote_match_backup, the newest backup
    matching the provided backup name and hostname of the node where
    freezer is executed. It correspond to the previous backup executed.
    NOTE: If backup has no tar_metadata, no newest backup is returned.
    """

    # Sort remote backup list using timestamp in reverse order,
    # that is from the newest to the oldest executed backup

    if not remote_match_backup:
        raise Exception("remote match backups are empty")
    sorted_backups_list = sort_backup_list(remote_match_backup)

    print sorted_backups_list

    for remote_obj in sorted_backups_list:
        obj_name_match = re.search(r'^{0}_({1})_(\d+)_\d+?$'.format(
            hostname, backup_name), remote_obj, re.I)
        print obj_name_match
        if not obj_name_match:
            continue
        tar_metadata_obj = 'tar_metadata_{0}'.format(remote_obj)
        if tar_metadata_obj in sorted_backups_list:
            return remote_obj
        raise Exception("no tar file")

    raise Exception('not backup found')
