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

from freezer.utils import (
    validate_all_args, get_match_backup,
    sort_backup_list)

import os
import swiftclient
import json
import re
from copy import deepcopy
import time
import logging
import sys

RESP_CHUNK_SIZE = 65536


def create_containers(backup_opt):
    """Create backup containers
    The function is used to create object and segments
    containers

    :param backup_opt:
    :return: True if both containers are successfully created
    """

    # Create backup container
    logging.warning(
        "[*] Creating container {0}".format(backup_opt.container))
    backup_opt.sw_connector.put_container(backup_opt.container)

    # Create segments container
    logging.warning(
        "[*] Creating container segments: {0}".format(
            backup_opt.container_segments))
    backup_opt.sw_connector.put_container(backup_opt.container_segments)

    return True


def show_containers(backup_opt_dict):
    """
    Print remote containers in sorted order
    """

    if not backup_opt_dict.list_container:
        return False

    ordered_container = {}
    for container in backup_opt_dict.containers_list:
        ordered_container['container_name'] = container['name']
        size = '{0}'.format((int(container['bytes']) / 1024) / 1024)
        if size == '0':
            size = '1'
        ordered_container['size'] = '{0}MB'.format(size)
        ordered_container['objects_count'] = container['count']
        print json.dumps(
            ordered_container, indent=4,
            separators=(',', ': '), sort_keys=True)
    return True


def show_objects(backup_opt_dict):
    """
    Retreive the list of backups from backup_opt_dict for the specified \
    container and print them nicely to std out.
    """

    if not backup_opt_dict.list_objects:
        return False

    required_list = [
        backup_opt_dict.remote_obj_list]

    if not validate_all_args(required_list):
        raise Exception('Remote Object list not avaiblale')

    ordered_objects = {}
    remote_obj = backup_opt_dict.remote_obj_list

    for obj in remote_obj:
        ordered_objects['object_name'] = obj['name']
        ordered_objects['upload_date'] = obj['last_modified']
        print json.dumps(
            ordered_objects, indent=4,
            separators=(',', ': '), sort_keys=True)

    return True


def remove_obj_older_than(backup_opt_dict):
    """
    Remove object in remote swift server older more tqhen days
    """

    if not backup_opt_dict.remote_obj_list \
            or backup_opt_dict.remove_older_than is False:
        logging.warning('[*] No remote objects will be removed')
        return False

    backup_opt_dict.remove_older_than = int(
        float(backup_opt_dict.remove_older_than))
    logging.info('[*] Removing object older {0} day(s)'.format(
        backup_opt_dict.remove_older_than))
    # Compute the amount of seconds from the number of days provided by
    # remove_older_than and compare it with the remote backup timestamp
    max_time = backup_opt_dict.remove_older_than * 86400
    current_timestamp = backup_opt_dict.time_stamp
    backup_name = backup_opt_dict.backup_name
    hostname = backup_opt_dict.hostname
    backup_opt_dict = get_match_backup(backup_opt_dict)
    sorted_remote_list = sort_backup_list(backup_opt_dict)
    sw_connector = backup_opt_dict.sw_connector

    level_0_flag = None
    tar_meta_0_flag = None
    for match_object in sorted_remote_list:
        obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
            hostname, backup_name), match_object, re.I)

        if obj_name_match:
            remote_obj_timestamp = int(obj_name_match.group(2))
            time_delta = current_timestamp - remote_obj_timestamp

            # If the difference between current_timestamp and the backup
            # timestamp is smaller then max_time, then the backup is valid
            if time_delta > max_time:

                # If the time_delta is bigger then max_time, then we verify
                # if the level of the backup is 0. In case is not 0,
                # the backup is not removed as is part of a backup where the
                # levels cross the max_time. In this case we don't remove the
                # backup till its level 0.
                # Both tar_meta data and backup objects names are handled
                if match_object.startswith('tar_meta'):
                    if tar_meta_0_flag is None:
                        if obj_name_match.group(3) is '0':
                            tar_meta_0_flag = True
                        else:
                            continue
                elif level_0_flag is None:
                    if obj_name_match.group(3) is '0':
                        level_0_flag = True
                    else:
                        continue

                logging.info('[*] Removing backup object: {0}'.format(
                    match_object))
                sleep_time = 120
                retry_max_count = 60
                curr_count = 0
                while True:
                    try:
                        sw_connector.delete_object(
                            backup_opt_dict.container, match_object)
                        logging.info(
                            '[*] Remote object {0} removed'.format(
                                match_object))
                        break
                    except Exception as error:
                        curr_count += 1
                        time.sleep(sleep_time)
                        if curr_count >= retry_max_count:
                            err_msg = (
                                '[*] Remote Object {0} failed to be removed.'
                                ' Retrying intent '
                                '{1} out of {2} totals'.format(
                                    match_object, curr_count,
                                    retry_max_count))
                            error_message = '[*] Error: {0}: {1}'.format(
                                err_msg, error)
                            raise Exception(error_message)
                        else:
                            logging.warning(
                                ('[*] Remote object {0} failed to be removed'
                                    ' Retrying intent n. '
                                    '{1} out of {2} totals'.format(
                                        match_object, curr_count,
                                        retry_max_count)))


def get_container_content(backup_opt_dict):
    """
    Download the list of object of the provided container
    and print them out as container meta-data and container object list
    """

    if not backup_opt_dict.container:
        raise Exception('please provide a valid container name')

    sw_connector = backup_opt_dict.sw_connector
    try:
        backup_opt_dict.remote_obj_list = \
            sw_connector.get_container(backup_opt_dict.container)[1]
        return backup_opt_dict
    except Exception as error:
        raise Exception('[*] Error: get_object_list: {0}'.format(error))


def check_container_existance(backup_opt_dict):
    """
    Check if the provided container is already available on Swift.
    The verification is done by exact matching between the provided container
    name and the whole list of container available for the swift account.
    If the container is not found, it will be automatically create and used
    to execute the backup
    """

    required_list = [
        backup_opt_dict.container_segments,
        backup_opt_dict.container]

    if not validate_all_args(required_list):
        raise Exception('please provide the following arg: --container')

    logging.info(
        "[*] Retrieving container {0}".format(backup_opt_dict.container))
    sw_connector = backup_opt_dict.sw_connector
    containers_list = sw_connector.get_account()[1]

    match_container = [
        container_object['name'] for container_object in containers_list
        if container_object['name'] == backup_opt_dict.container]
    match_container_seg = [
        container_object['name'] for container_object in containers_list
        if container_object['name'] == backup_opt_dict.container_segments]

    # Initialize container dict
    containers = {'main_container': False, 'container_segments': False}

    if not match_container:
        logging.warning("[*] No such container {0} available... ".format(
            backup_opt_dict.container))
    else:
        logging.info(
            "[*] Container {0} found!".format(backup_opt_dict.container))
        containers['main_container'] = True

    if not match_container_seg:
        logging.warning(
            "[*] No segments container {0} available...".format(
                backup_opt_dict.container_segments))
    else:
        logging.info("[*] Container Segments {0} found!".format(
            backup_opt_dict.container_segments))
        containers['container_segments'] = True

    return containers


def get_swift_os_env():
    """
    Get the swift related environment variable
    """

    environ_dict = os.environ
    try:
        return environ_dict['OS_REGION_NAME'], environ_dict['OS_TENANT_ID'],\
            environ_dict['OS_PASSWORD'], environ_dict['OS_AUTH_URL'],\
            environ_dict['OS_USERNAME'], environ_dict['OS_TENANT_NAME']
    except Exception as e:
        raise Exception('missing environment variable {0}'.format(e))


def get_client(backup_opt_dict):
    """
    Initialize a swift client object and return it in
    backup_opt_dict
    """

    sw_client = swiftclient.client
    options = {}
    (options['region_name'], options['tenant_id'], options['password'],
        options['auth_url'], options['username'],
        options['tenant_name']) = get_swift_os_env()

    backup_opt_dict.sw_connector = sw_client.Connection(
        authurl=options['auth_url'],
        user=options['username'], key=options['password'], os_options=options,
        tenant_name=options['tenant_name'], auth_version='2', retries=6)

    return backup_opt_dict


def manifest_upload(
        manifest_file, backup_opt_dict, file_prefix, manifest_meta_dict):
    """
    Upload Manifest to manage segments in Swift
    """

    if not manifest_meta_dict:
        raise Exception('Manifest Meta dictionary not available')

    sw_connector = backup_opt_dict.sw_connector
    tmp_manifest_meta = dict()
    for key, value in manifest_meta_dict.items():
        if key.startswith('x-object-meta'):
            tmp_manifest_meta[key] = value
    manifest_meta_dict = deepcopy(tmp_manifest_meta)
    header = manifest_meta_dict
    manifest_meta_dict['x-object-manifest'] = u'{0}/{1}'.format(
        backup_opt_dict.container_segments.strip(), file_prefix.strip())
    logging.info('[*] Uploading Swift Manifest: {0}'.format(header))
    sw_connector.put_object(
        backup_opt_dict.container, file_prefix, manifest_file, headers=header)
    logging.info('[*] Manifest successfully uploaded!')


def add_object(
    backup_opt_dict, backup_queue, absolute_file_path=None,
        time_stamp=None):
    """
    Upload object on the remote swift server
    """

    if not backup_opt_dict.container:
        err_msg = ('[*] Error: Please specify the container '
                   'name with -C or --container option')
        logging.exception(err_msg)
        sys.exit(1)

    if absolute_file_path is None and backup_queue is None:
        err_msg = ('[*] Error: Please specify the file or fs path '
                   'you want to upload on swift with -d or --dst-file')
        logging.exception(err_msg)
        sys.exit(1)

    sw_connector = backup_opt_dict.sw_connector
    while True:
        package_name = absolute_file_path.split('/')[-1]
        file_chunk_index, file_chunk = backup_queue.get().popitem()
        if not file_chunk_index and not file_chunk:
            break
        package_name = u'{0}/{1}/{2}/{3}'.format(
            package_name, time_stamp,
            backup_opt_dict.max_seg_size, file_chunk_index)
        # If for some reason the swift client object is not available anymore
        # an exception is generated and a new client object is initialized/
        # If the exception happens for 10 consecutive times for a total of
        # 1 hour, then the program will exit with an Exception.
        count = 0
        while True:
            try:
                logging.info(
                    '[*] Uploading file chunk index: {0}'.format(
                        package_name))
                sw_connector.put_object(
                    backup_opt_dict.container_segments,
                    package_name, file_chunk,
                    content_type='application/octet-stream',
                    content_length=len(file_chunk))
                logging.info('[*] Data successfully uploaded!')
                break
            except Exception as error:
                time.sleep(60)
                logging.info(
                    '[*] Retrying to upload file chunk index: {0}'.format(
                        package_name))
                backup_opt_dict = get_client(backup_opt_dict)
                count += 1
                if count == 10:
                    logging.critical('[*] Error: add_object: {0}'
                                     .format(error))
                    sys.exit(1)


def get_containers_list(backup_opt_dict):
    """
    Get a list and information of all the available containers
    """

    try:
        sw_connector = backup_opt_dict.sw_connector
        backup_opt_dict.containers_list = sw_connector.get_account()[1]
        return backup_opt_dict
    except Exception as error:
        raise Exception('Get containers list error: {0}'.format(error))


def object_to_file(backup_opt_dict, file_name_abs_path):
    """
    Take a payload downloaded from Swift
    and save it to the disk as file_name
    """

    required_list = [
        backup_opt_dict.container,
        file_name_abs_path]

    if not validate_all_args(required_list):
        raise ValueError('Error in object_to_file(): Please provide ALL the '
                         'following arguments: --container file_name_abs_path')

    sw_connector = backup_opt_dict.sw_connector
    file_name = file_name_abs_path.split('/')[-1]
    logging.info('[*] Downloading object {0} on {1}'.format(
        file_name, file_name_abs_path))

    # As the file is download by chunks and each chunk will be appened
    # to file_name_abs_path, we make sure file_name_abs_path does not
    # exists by removing it before
    if os.path.exists(file_name_abs_path):
        os.remove(file_name_abs_path)

    with open(file_name_abs_path, 'ab') as obj_fd:
        for obj_chunk in sw_connector.get_object(
                backup_opt_dict.container, file_name,
                resp_chunk_size=16000000)[1]:
            obj_fd.write(obj_chunk)

    return True


def object_to_stream(backup_opt_dict, write_pipe, read_pipe, obj_name):
    """
    Take a payload downloaded from Swift
    and generate a stream to be consumed from other processes
    """

    required_list = [
        backup_opt_dict.container]

    if not validate_all_args(required_list):
        raise ValueError('Error in object_to_stream(): Please provide '
                         'ALL the following argument: --container')

    backup_opt_dict = get_client(backup_opt_dict)
    logging.info('[*] Downloading data stream...')

    # Close the read pipe in this child as it is unneeded
    # and download the objects from swift in chunks. The
    # Chunk size is set by RESP_CHUNK_SIZE and sent to che write
    # pipe
    read_pipe.close()
    for obj_chunk in backup_opt_dict.sw_connector.get_object(
            backup_opt_dict.container, obj_name,
            resp_chunk_size=RESP_CHUNK_SIZE)[1]:

        write_pipe.send_bytes(obj_chunk)

    # Closing the pipe after checking no data
    # is still vailable in the pipe.
    while True:
        if not write_pipe.poll():
            write_pipe.close()
            break
        time.sleep(1)
