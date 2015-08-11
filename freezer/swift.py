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
"""

from copy import deepcopy
import multiprocessing

from freezer import utils
from freezer import tar
import json
import time
import logging
import os
from freezer import storage


class SwiftStorage(storage.Storage):
    """
    :type client_manager: freezer.osclients.ClientManager
    """

    def __init__(self, client_manager, container, work_dir, max_segment_size):
        """
        :type client_manager: freezer.osclients.ClientManager
        :type container: str
        """
        self.client_manager = client_manager
        self.container = container
        self.segments = u'{0}_segments'.format(container)
        self.work_dir = work_dir
        self.max_segment_size = max_segment_size

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

    def upload_manifest(self, name, headers=None):
        """
        Upload Manifest to manage segments in Swift

        :param name: Name of manifest file
        :type name: str
        """

        self.client_manager.create_swift()
        headers = deepcopy(headers) or dict()
        headers['x-object-manifest'] = u'{0}/{1}'.format(self.segments,
                                                         name.strip())
        logging.info('[*] Uploading Swift Manifest: {0}'.format(name))
        self.swift().put_object(container=self.container, obj=name,
                                contents=u'', headers=headers)
        logging.info('[*] Manifest successfully uploaded!')

    def is_ready(self):
        return self.check_container_existence()[0]

    def restore(self, backup, path, tar_builder):
        """
        Restore data from swift server to your local node. Data will be
        restored in the directory specified in
        backup_opt_dict.restore_abs_path. The
        object specified with the --get-object option will be downloaded from
        the Swift server and will be downloaded inside the parent directory of
        backup_opt_dict.restore_abs_path. If the object was compressed during
        backup time, then it is decrypted, decompressed and de-archived to
        backup_opt_dict.restore_abs_path. Before download the file, the size of
        the local volume/disk/partition will be computed. If there is enough
        space
        the full restore will be executed. Please remember to stop any service
        that require access to the data before to start the restore execution
        and to start the service at the end of the restore execution

          Take options dict as argument and sort/remove duplicate elements from
        backup_opt_dict.remote_match_backup and find the closes backup to the
        provided from backup_opt_dict.restore_from_date. Once the objects are
        looped backwards and the level 0 backup is found, along with the other
        level 1,2,n, is download the object from swift and untar them locally
        starting from level 0 to level N.
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        """

        for level in range(0, backup.level + 1):
            self._restore(backup.parent.increments[level], path, tar_builder)

    def _restore(self, backup, path, tar_builder):
        """
        :type backup: freezer.storage.Backup
        :param backup:
        :type path: str
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        :return:
        """
        write_pipe, read_pipe = multiprocessing.Pipe()
        process_stream = multiprocessing.Process(
            target=self.object_to_stream,
            args=(write_pipe, read_pipe, backup.repr(),))
        process_stream.daemon = True
        process_stream.start()

        write_pipe.close()
        # Start the tar pipe consumer process
        tar_stream = multiprocessing.Process(
            target=tar.tar_restore, args=(path, tar_builder.build(),
                                          read_pipe))
        tar_stream.daemon = True
        tar_stream.start()
        read_pipe.close()
        process_stream.join()
        tar_stream.join()

        if tar_stream.exitcode:
            raise Exception('failed to restore file')

        logging.info(
            '[*] Restore execution successfully executed \
             for backup name {0}'.format(backup.repr()))

    def prepare(self):
        containers = self.check_container_existence()
        if not containers[0]:
            self.swift().put_container(self.container)
        if not containers[1]:
            self.swift().put_container(self.segments)

    def check_container_existence(self):
        """
        Check if the provided container is already available on Swift.
        The verification is done by exact matching between the provided
        container name and the whole list of container available for the swift
        account.
        """
        containers_list = [c['name'] for c in self.swift().get_account()[1]]
        return (self.container in containers_list,
                self.segments in containers_list)

    def add_object(self, backup_queue, current_backup):
        """
        Upload object on the remote swift server
        :type current_backup: SwiftBackup
        """
        file_chunk_index, file_chunk = backup_queue.get().popitem()
        while file_chunk_index or file_chunk:
            segment_package_name = u'{0}/{1}/{2}/{3}'.format(
                current_backup.repr(), current_backup.timestamp,
                self.max_segment_size, file_chunk_index)
            self.upload_chunk(file_chunk, segment_package_name)
            file_chunk_index, file_chunk = backup_queue.get().popitem()

    RESP_CHUNK_SIZE = 65536

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

    def remove_backup(self, backup):
        """
            Removes backup, all increments, tar_meta and segments
            :param backup:
            :return:
        """
        for i in range(backup.latest_update.level, -1, -1):
            if i in backup.increments:
                # remove segment
                for segment in self.swift().get_container(
                        self.segments,
                        prefix=backup.increments[i].repr())[1]:
                    self.swift().delete_object(self.segments, segment['name'])

                # remove tar
                for segment in self.swift().get_container(
                        self.container,
                        prefix=backup.increments[i].tar())[1]:
                    self.swift().delete_object(self.container, segment['name'])

                # remove manifest
                for segment in self.swift().get_container(
                        self.container,
                        prefix=backup.increments[i].repr())[1]:
                    self.swift().delete_object(self.container, segment['name'])

    def add_stream(self, stream, package_name, headers=None):
        i = 0

        for el in stream:
            self.upload_chunk("{0}/{1}".format(package_name, "%08d" % i), el)
            i += 1
        if not headers:
            headers = {}
        headers['X-Object-Manifest'] = u'{0}/{1}/'.format(
            self.segments, package_name)
        headers['x-object-meta-length'] = len(stream)

        self.swift().put_object(self.container, package_name, "",
                                headers=headers)

    def object_to_stream(self, write_pipe, read_pipe, obj_name):
        """
        Take a payload downloaded from Swift
        and generate a stream to be consumed from other processes
        """
        logging.info('[*] Downloading data stream...')

        # Close the read pipe in this child as it is unneeded
        # and download the objects from swift in chunks. The
        # Chunk size is set by RESP_CHUNK_SIZE and sent to che write
        # pipe
        read_pipe.close()
        for obj_chunk in self.swift().get_object(
                self.container, obj_name,
                resp_chunk_size=self.RESP_CHUNK_SIZE)[1]:
            write_pipe.send_bytes(obj_chunk)

        # Closing the pipe after checking no data
        # is still available in the pipe.
        while True:
            if not write_pipe.poll():
                write_pipe.close()
                break
            time.sleep(1)

    def get_backups(self):
        """
        :rtype: list[SwiftBackup]
        :return: list of zero level backups
        """
        try:
            files = self.swift().get_container(self.container)[1]
            names = [x['name'] for x in files if 'name' in x]
            return self._get_backups(names)
        except Exception as error:
            raise Exception('[*] Error: get_object_list: {0}'.format(error))

    def get_last_backup(self, hostname_backup_name):
        """

        :param hostname_backup_name:
        :return: last backup or throws exception
        :rtype: freezer.swift.backup.SwiftBackup
        """
        return max(self.find(hostname_backup_name), key=lambda b: b.timestamp)

    def _download_tar_meta(self, backup):
        """
        Downloads meta_data to work_dir of previous backup.

        :param backup: A backup or increment. Current backup is incremental,
        that means we should download tar_meta for detection new files and
        changes. If backup.tar_meta is false, raise Exception
        :type backup: SwiftBackup
        :return:
        """
        if not backup.tar_meta:
            raise ValueError('Latest update have no tar_meta')

        utils.create_dir(self.work_dir)
        tar_meta = backup.tar()
        tar_meta_abs = "{0}/{1}".format(self.work_dir, tar_meta)

        logging.info('[*] Downloading object {0} {1}'.format(
            tar_meta, tar_meta_abs))

        if os.path.exists(tar_meta_abs):
            os.remove(tar_meta_abs)

        with open(tar_meta_abs, 'ab') as obj_fd:
            iterator = self.swift().get_object(
                self.container, tar_meta, resp_chunk_size=16000000)[1]
            for obj_chunk in iterator:
                obj_fd.write(obj_chunk)

    def _execute_tar_and_upload(self, path_to_backup, current_backup,
                                tar_command):
        """

        :param path_to_backup:
        :type path_to_backup: str
        :param current_backup:
        :type current_backup: freezer.storage.Backup
        :param tar_command:
        :type tar_command: str
        :return:
        """
        # Initialize a Queue for a maximum of 2 items
        tar_backup_queue = multiprocessing.Queue(maxsize=2)

        logging.info('[*] Changing current working directory to: {0} \
        '.format(path_to_backup))
        logging.info('[*] Backup started for: {0}'.format(path_to_backup))

        tar_backup_stream = multiprocessing.Process(
            target=tar.tar_backup, args=(path_to_backup,
                                         self.max_segment_size,
                                         tar_command,
                                         tar_backup_queue))

        tar_backup_stream.daemon = True
        tar_backup_stream.start()

        add_object_stream = multiprocessing.Process(
            target=self.add_object, args=(tar_backup_queue, current_backup))
        add_object_stream.daemon = True
        add_object_stream.start()

        tar_backup_stream.join()
        tar_backup_queue.put(({False: False}))
        tar_backup_queue.close()
        add_object_stream.join()

        if add_object_stream.exitcode:
            raise Exception('failed to upload object to swift server')

    def _upload_tar_meta(self, new_backup, old_backup):
        meta_data_abs_path = os.path.join(self.work_dir, old_backup.tar())

        # Upload swift manifest for segments
        # Request a new auth client in case the current token
        # is expired before uploading tar meta data or the swift manifest
        self.client_manager.create_swift()

        # Upload tar incremental meta data file and remove it
        logging.info('[*] Uploading tar meta data file: {0}'.format(
            new_backup.tar()))
        with open(meta_data_abs_path, 'r') as meta_fd:
            self.swift().put_object(
                self.container, new_backup.tar(), meta_fd)
        # Removing tar meta data file, so we have only one
        # authoritative version on swift
        logging.info('[*] Removing tar meta data file: {0}'.format(
            meta_data_abs_path))
        os.remove(meta_data_abs_path)

    def backup(self, path, hostname_backup_name, tar_builder,
               parent_backup=None):
        new_backup = self._create_backup(hostname_backup_name, parent_backup)

        if parent_backup:
            self._download_tar_meta(parent_backup)
        tar_builder.set_listed_incremental(
            "{0}/{1}".format(self.work_dir,
                             (parent_backup or new_backup).tar()))

        self._execute_tar_and_upload(path, new_backup, tar_builder.build())
        self._upload_tar_meta(new_backup, parent_backup or new_backup)
        self.upload_manifest(new_backup.repr())
