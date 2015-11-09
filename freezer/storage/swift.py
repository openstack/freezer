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

import json
import time
import logging
import os

from freezer import utils
from freezer.storage import storage


class SwiftStorage(storage.Storage):
    """
    :type client_manager: freezer.osclients.ClientManager
    """

    RESP_CHUNK_SIZE = 10000000

    def __init__(self, client_manager, container, work_dir, max_segment_size,
                 chunk_size=RESP_CHUNK_SIZE):
        """
        :type client_manager: freezer.osclients.ClientManager
        :type container: str
        """
        self.client_manager = client_manager
        self.container = container
        self.segments = u'{0}_segments'.format(container)
        self.work_dir = work_dir
        self.max_segment_size = max_segment_size
        self.chunk_size = chunk_size

    def swift(self):
        """
        :rtype: swiftclient.Connection
        :return:
        """
        return self.client_manager.get_swift()

    def upload_chunk(self, content, path):
        """
        """
        # If for some reason the swift client object is not available anymore
        # an exception is generated and a new client object is initialized/
        # If the exception happens for 10 consecutive times for a total of
        # 1 hour, then the program will exit with an Exception.

        count = 0
        success = False
        while not success:
            try:
                logging.info(
                    '[*] Uploading file chunk index: {0}'.format(path))
                self.swift().put_object(
                    self.segments, path, content,
                    content_type='application/octet-stream',
                    content_length=len(content))
                logging.info('[*] Data successfully uploaded!')
                success = True
            except Exception as error:
                logging.info(
                    '[*] Retrying to upload file chunk index: {0}'.format(
                        path))
                time.sleep(60)
                self.client_manager.create_swift()
                count += 1
                if count == 10:
                    logging.critical('[*] Error: add_object: {0}'
                                     .format(error))
                    raise Exception("cannot add object to storage")

    def upload_manifest(self, backup):
        """
        Upload Manifest to manage segments in Swift

        :param backup: Backup
        :type backup: freezer.storage.Backup
        """
        self.client_manager.create_swift()
        headers = {'x-object-manifest':
                   u'{0}/{1}'.format(self.segments, backup)}
        logging.info('[*] Uploading Swift Manifest: {0}'.format(backup))
        self.swift().put_object(container=self.container, obj=str(backup),
                                contents=u'', headers=headers)
        logging.info('[*] Manifest successfully uploaded!')

    def upload_meta_file(self, backup, meta_file):
        # Upload swift manifest for segments
        # Request a new auth client in case the current token
        # is expired before uploading tar meta data or the swift manifest
        self.client_manager.create_swift()

        # Upload tar incremental meta data file and remove it
        logging.info('[*] Uploading tar meta data file: {0}'.format(
            backup.tar()))
        with open(meta_file, 'r') as meta_fd:
            self.swift().put_object(
                self.container, backup.tar(), meta_fd)

    def prepare(self):
        """
        Check if the provided container is already available on Swift.
        The verification is done by exact matching between the provided
        container name and the whole list of container available for the swift
        account.
        """
        containers_list = [c['name'] for c in self.swift().get_account()[1]]
        if self.container not in containers_list:
            self.swift().put_container(self.container)
        if self.segments not in containers_list:
            self.swift().put_container(self.segments)

    def info(self):
        ordered_container = {}
        containers = self.swift().get_account()[1]
        for container in containers:
            print container
            ordered_container['container_name'] = container['name']
            size = '{0}'.format((int(container['bytes']) / 1024) / 1024)
            if size == '0':
                size = '1'
            ordered_container['size'] = '{0}MB'.format(size)
            ordered_container['objects_count'] = container['count']
            print json.dumps(
                ordered_container, indent=4,
                separators=(',', ': '), sort_keys=True)

    def remove(self, container, prefix):
        for segment in self.swift().get_container(container, prefix=prefix)[1]:
            self.swift().delete_object(container, segment['name'])

    def remove_backup(self, backup):
        """
            Removes backup, all increments, tar_meta and segments
            :param backup:
            :return:
        """
        for i in range(backup.latest_update.level, -1, -1):
            if i in backup.increments:
                # remove segment
                self.remove(self.segments, backup.increments[i])
                # remove tar
                self.remove(self.container, backup.increments[i].tar())
                # remove manifest
                self.remove(self.container, backup.increments[i])

    def add_stream(self, stream, package_name, headers=None):
        i = 0
        for el in stream:
            self.upload_chunk(el, "{0}/{1}".format(package_name, "%08d" % i))
            i += 1
        if not headers:
            headers = {}
        headers['X-Object-Manifest'] = u'{0}/{1}/'.format(
            self.segments, package_name)
        headers['x-object-meta-length'] = len(stream)

        self.swift().put_object(self.container, package_name, "",
                                headers=headers)

    def get_backups(self):
        """
        :rtype: list[SwiftBackup]
        :return: list of zero level backups
        """
        try:
            files = self.swift().get_container(self.container)[1]
            names = [x['name'] for x in files if 'name' in x]
            return storage.Backup.parse_backups(names)
        except Exception as error:
            raise Exception('[*] Error: get_object_list: {0}'.format(error))

    def download_meta_file(self, backup):
        """
        Downloads meta_data to work_dir of previous backup.

        :param backup: A backup or increment. Current backup is incremental,
        that means we should download tar_meta for detection new files and
        changes. If backup.tar_meta is false, raise Exception
        :type backup: freezer.storage.Backup
        :return:
        """
        utils.create_dir(self.work_dir)
        if backup.level == 0:
            return "{0}{1}{2}".format(self.work_dir, os.sep, backup.tar())

        meta_backup = backup.full_backup.increments[backup.level - 1]

        if not meta_backup.tar_meta:
            raise ValueError('Latest update have no tar_meta')

        tar_meta = meta_backup.tar()
        tar_meta_abs = "{0}{1}{2}".format(self.work_dir, os.sep, tar_meta)

        logging.info('[*] Downloading object {0} {1}'.format(
            tar_meta, tar_meta_abs))

        if os.path.exists(tar_meta_abs):
            os.remove(tar_meta_abs)

        with open(tar_meta_abs, 'ab') as obj_fd:
            iterator = self.swift().get_object(
                self.container, tar_meta, resp_chunk_size=self.chunk_size)[1]
            for obj_chunk in iterator:
                obj_fd.write(obj_chunk)
        return tar_meta_abs

    def backup_blocks(self, backup):
        for chunk in self.swift().get_object(
                self.container, backup, resp_chunk_size=self.chunk_size)[1]:
            yield chunk

    def write_backup(self, rich_queue, backup):
        """
        Upload object on the remote swift server
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: SwiftBackup
        """
        for block_index, message in enumerate(rich_queue.get_messages()):
            segment_package_name = u'{0}/{1}/{2}/{3}'.format(
                backup, backup.timestamp,
                self.max_segment_size, "%08d" % block_index)
            self.upload_chunk(message, segment_package_name)
        self.upload_manifest(backup)
