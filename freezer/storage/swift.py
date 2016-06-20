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
from oslo_log import log
import requests.exceptions
import time

from freezer.storage import base

LOG = log.getLogger(__name__)


class SwiftStorage(base.Storage):
    """
    :type client_manager: freezer.osclients.ClientManager
    """

    def __init__(self, client_manager, container, work_dir, max_segment_size,
                 skip_prepare=False):
        """
        :type client_manager: freezer.osclients.ClientManager
        :type container: str
        """
        self.client_manager = client_manager
        # The containers used by freezer to executed backups needs to have
        # freezer_ prefix in the name. If the user provider container doesn't
        # have the prefix, it is automatically added also to the container
        # segments name. This is done to quickly identify the containers
        # that contain freezer generated backups
        if not container.startswith('freezer_'):
            self.container = 'freezer_{0}'.format(container)
        else:
            self.container = container
        self.segments = u'{0}_segments'.format(container)
        self.max_segment_size = max_segment_size
        super(SwiftStorage, self).__init__(work_dir, skip_prepare)

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
                LOG.info(
                    'Uploading file chunk index: {0}'.format(path))
                self.swift().put_object(
                    self.segments, path, content,
                    content_type='application/octet-stream',
                    content_length=len(content))
                LOG.info('Data successfully uploaded!')
                success = True
            except Exception as error:
                LOG.info(
                    'Retrying to upload file chunk index: {0}'.format(
                        path))
                time.sleep(60)
                self.client_manager.create_swift()
                count += 1
                if count == 10:
                    LOG.critical('Error: add_object: {0}'
                                 .format(error))
                    raise Exception("cannot add object to storage")

    def upload_manifest(self, backup):
        """
        Upload Manifest to manage segments in Swift

        :param backup: Backup
        :type backup: freezer.storage.base.Backup
        """
        self.client_manager.create_swift()
        headers = {'x-object-manifest':
                   u'{0}/{1}'.format(self.segments, backup)}
        LOG.info('Uploading Swift Manifest: {0}'.format(backup))
        self.swift().put_object(container=self.container, obj=str(backup),
                                contents=u'', headers=headers)
        LOG.info('Manifest successfully uploaded!')

    def upload_meta_file(self, backup, meta_file):
        # Upload swift manifest for segments
        # Request a new auth client in case the current token
        # is expired before uploading tar meta data or the swift manifest
        self.client_manager.create_swift()

        # Upload tar incremental meta data file and remove it
        LOG.info('Uploading tar meta data file: {0}'.format(
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
            print(container)
            ordered_container['container_name'] = container['name']
            size = '{0}'.format((int(container['bytes']) / 1024) / 1024)
            if size == '0':
                size = '1'
            ordered_container['size'] = '{0}MB'.format(size)
            ordered_container['objects_count'] = container['count']
            print(json.dumps(
                ordered_container, indent=4,
                separators=(',', ': '), sort_keys=True))

    def meta_file_abs_path(self, backup):
        return backup.tar()

    def get_file(self, from_path, to_path):
        with open(to_path, 'ab') as obj_fd:
            iterator = self.swift().get_object(
                self.container, from_path,
                resp_chunk_size=self.max_segment_size)[1]
            for obj_chunk in iterator:
                obj_fd.write(obj_chunk)

    def remove(self, container, prefix):
        for segment in self.swift().get_container(container, prefix=prefix)[1]:
            self.swift().delete_object(container, segment['name'])

    def remove_backup(self, backup):
        """
            Removes backup, all increments, tar_meta and segments
            :param backup:
            :type backup: freezer.storage.base.Backup
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

    def find_all(self, hostname_backup_name):
        """
        :rtype: list[freezer.storage.base.Backup]
        :return: list of zero level backups
        """
        try:
            files = self.swift().get_container(self.container)[1]
            names = [x['name'] for x in files if 'name' in x]
            return [b for b in base.Backup.parse_backups(names, self)
                    if b.hostname_backup_name == hostname_backup_name]
        except Exception as error:
            raise Exception('Error: get_object_list: {0}'.format(error))

    def backup_blocks(self, backup):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        try:
            chunks = self.swift().get_object(
                self.container, str(backup),
                resp_chunk_size=self.max_segment_size)[1]
        except requests.exceptions.SSLError as e:
            LOG.warning(e)
            chunks = self.client_manager.create_swift().get_object(
                self.container, str(backup),
                resp_chunk_size=self.max_segment_size)[1]

        for chunk in chunks:
            yield chunk

    def write_backup(self, rich_queue, backup):
        """
        Upload object on the remote swift server
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        for block_index, message in enumerate(rich_queue.get_messages()):
            segment_package_name = u'{0}/{1}/{2}/{3}'.format(
                backup, backup.timestamp,
                self.max_segment_size, "%08d" % block_index)
            self.upload_chunk(message, segment_package_name)
        self.upload_manifest(backup)

    def download_freezer_meta_data(self, backup):
        return {}

    def upload_freezer_meta_data(self, backup, meta_dict):
        pass
