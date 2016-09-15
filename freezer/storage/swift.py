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

from freezer.storage import physical

LOG = log.getLogger(__name__)


class SwiftStorage(physical.PhysicalStorage):
    """
    :type client_manager: freezer.osclients.ClientManager
    """

    def rmtree(self, path):
        split = path.rsplit('/', 1)
        for file in self.swift().get_container(split[0],
                                               prefix=split[1])[1]:
            try:
                self.swift().delete_object(split[0], file['name'])
            except Exception as e:
                raise e

    def put_file(self, from_path, to_path):
        self.client_manager.create_swift()
        split = to_path.rsplit('/', 1)
        with open(from_path, 'r') as meta_fd:
            self.swift().put_object(split[0], split[1], meta_fd)

    def __init__(self, client_manager, container, max_segment_size,
                 skip_prepare=False):
        """
        :type client_manager: freezer.osclients.OSClientManager
        :type container: str
        """
        self.client_manager = client_manager
        super(SwiftStorage, self).__init__(
            storage_path=container,
            max_segment_size=max_segment_size,
            skip_prepare=skip_prepare)
        self.container = container
        self.segments = "{0}_segments".format(container)

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
        split = path.rsplit('/', 1)
        while not success:
            try:
                LOG.info(
                    'Uploading file chunk index: {0}'.format(path))
                self.swift().put_object(
                    split[0], split[1], content,
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
        backup = backup.copy(storage=self)
        self.client_manager.create_swift()
        headers = {'x-object-manifest': backup.segments_path}
        LOG.info('[*] Uploading Swift Manifest: {0}'.format(backup))
        split = backup.data_path.rsplit('/', 1)
        self.swift().put_object(container=split[0], obj=split[1],
                                contents=u'', headers=headers)
        LOG.info('Manifest successfully uploaded!')

    def prepare(self):
        """
        Check if the provided container is already available on Swift.
        The verification is done by exact matching between the provided
        container name and the whole list of container available for the swift
        account.
        """
        containers_list = [c['name'] for c in self.swift().get_account()[1]]
        if self.storage_path not in containers_list:
            self.swift().put_container(self.storage_path)

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

    def get_file(self, from_path, to_path):
        split = from_path.split('/', 1)
        with open(to_path, 'ab') as obj_fd:
            iterator = self.swift().get_object(
                split[0], split[1],
                resp_chunk_size=self.max_segment_size)[1]
            for obj_chunk in iterator:
                obj_fd.write(obj_chunk)

    def add_stream(self, stream, package_name, headers=None):
        i = 0
        backup_basepath = "{0}/{1}".format(self.container, self.segments)
        for el in stream:
            upload_path = "{0}/{1}/segments/{2}".format(backup_basepath,
                                                        package_name,
                                                        "%08d" % i)
            self.upload_chunk(el, upload_path)
            i += 1
        if not headers:
            headers = {}

        full_path = "{0}/{1}".format(backup_basepath, package_name)
        headers['x-object-manifest'] = full_path
        headers['x-object-meta-length'] = str(len(stream))

        objname = package_name.rsplit('/', 1)[1]
        # This call sets the metadata on a file which will be used to download
        # the whole backup later. Do not remove it ! (szaher)
        self.swift().put_object(container=full_path, obj=objname, contents=u'',
                                headers=headers)

    def backup_blocks(self, backup):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        split = backup.data_path.split('/', 1)
        try:
            chunks = self.client_manager.create_swift().get_object(
                split[0], split[1],
                resp_chunk_size=self.max_segment_size)[1]
        except requests.exceptions.SSLError as e:
            LOG.warning(e)
            chunks = self.client_manager.create_swift().get_object(
                split[0], split[1],
                resp_chunk_size=self.max_segment_size)[1]

        for chunk in chunks:
            yield chunk

    def write_backup(self, rich_queue, backup):
        """
        Upload object on the remote swift server
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        backup = backup.copy(storage=self)
        for block_index, message in enumerate(rich_queue.get_messages()):
            segment_package_name = u'{0}/{1}'.format(
                backup.segments_path, "%08d" % block_index)
            self.upload_chunk(message, segment_package_name)
        self.upload_manifest(backup)

    def listdir(self, path):
        """
        :type path: str
        :param path:
        :rtype: collections.Iterable[str]
        """
        try:
            # split[0] will have container name and the split[1] will have
            # the rest of the path. If the path is
            # freezer_backups/tar/server1.cloud.com_testest/
            # split[0] = freezer_backups which is container name
            # split[1] = tar/server1.cloud.com_testest/
            split = path.split('/', 1)
            files = self.swift().get_container(container=split[0],
                                               full_listing=True,
                                               prefix=split[1])[1]
            # @todo normalize intro plain for loop to be easily
            # understandable (szaher)
            return set(f['name'][len(split[1]):].split('/', 2)[1] for f in
                       files)
        except Exception as e:
            LOG.info(e)
            return []

    def create_dirs(self, folder_list):
        pass
