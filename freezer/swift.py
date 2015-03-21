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
    sort_backup_list, DateTime)

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
            if curr_count >= retry_max_count:
                err_msg = (
                    '[*] Remote Object {0} failed to be removed.'
                    ' Retrying intent '
                    '{1} out of {2} totals'.format(
                        obj, curr_count,
                        retry_max_count))
                error_message = \
                    '[*] Error: {0}: {1}'.format(err_msg, error)
                raise Exception(error_message)
            else:
                logging.warning(
                    ('[*] Remote object {0} failed to be removed'
                     ' Retrying intent n. {1} out of {2} totals'.format(
                         obj, curr_count, retry_max_count)))


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

    if not backup_opt_dict.remote_obj_list:
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
    backup_opt_dict = get_match_backup(backup_opt_dict)
    sorted_remote_list = sort_backup_list(backup_opt_dict)

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
                        (obj_name_match.group(3) is not '0')
                else:
                    incremental_dep_flag = \
                        (obj_name_match.group(3) is not '0')

            else:
                if match_object.startswith('tar_meta'):
                    if not tar_meta_incremental_dep_flag:
                        remove_object(backup_opt_dict.sw_connector,
                                      backup_opt_dict.container, match_object)
                    else:
                        if obj_name_match.group(3) is '0':
                            tar_meta_incremental_dep_flag = False
                else:
                    if not incremental_dep_flag:
                        remove_object(backup_opt_dict.sw_connector,
                                      backup_opt_dict.container, match_object)
                    else:
                        if obj_name_match.group(3) is '0':
                            incremental_dep_flag = False


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


class DryRunSwiftclientConnectionWrapper:
    def __init__(self, sw_connector):
        self.sw_connector = sw_connector
        self.get_object = sw_connector.get_object
        self.get_account = sw_connector.get_account
        self.get_container = sw_connector.get_container
        self.head_object = sw_connector.head_object
        self.put_object = self.dummy
        self.put_container = self.dummy
        self.delete_object = self.dummy

    def dummy(self, *args, **kwargs):
        pass


class SwiftOptions:

    @property
    def os_options(self):
        """
        :return: The OpenStack options which can have tenant_id,
                 auth_token, service_type, endpoint_type, tenant_name,
                 object_storage_url, region_name
        """
        return {'tenant_id': self.tenant_id,
                'tenant_name': self.tenant_name,
                'region_name': self.region_name}

    @staticmethod
    def create_from_dict(src_dict):
        options = SwiftOptions()
        try:
            options.user_name = src_dict['OS_USERNAME']
            options.tenant_name = src_dict['OS_TENANT_NAME']
            options.auth_url = src_dict['OS_AUTH_URL']
            options.password = src_dict['OS_PASSWORD']
            options.tenant_id = src_dict.get('OS_TENANT_ID', None)
            options.region_name = src_dict.get('OS_REGION_NAME', None)
        except Exception as e:
            raise Exception('missing swift connection parameter: {0}'
                            .format(e))
        return options


def get_client(backup_opt_dict):
    """
    Initialize a swift client object and return it in
    backup_opt_dict
    """

    options = SwiftOptions.create_from_dict(os.environ)

    backup_opt_dict.sw_connector = swiftclient.client.Connection(
        authurl=options.auth_url,
        user=options.user_name, key=options.password,
        tenant_name=options.tenant_name,
        os_options=options.os_options,
        auth_version=backup_opt_dict.auth_version,
        insecure=backup_opt_dict.insecure, retries=6)

    if backup_opt_dict.dry_run:
        backup_opt_dict.sw_connector =\
            DryRunSwiftclientConnectionWrapper(backup_opt_dict.sw_connector)

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
