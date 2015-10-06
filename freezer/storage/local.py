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

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
"""

import os
import shutil
import io
import logging

from freezer.storage import storage
from freezer import utils


class LocalStorage(storage.Storage):
    DEFAULT_CHUNK_SIZE = 20000000

    def __init__(self, storage_directory, work_dir,
                 chunk_size=DEFAULT_CHUNK_SIZE):
        """
        :param storage_directory: directory of storage
        :type storage_directory: str
        :return:
        """
        self.storage_directory = storage_directory
        self.work_dir = work_dir
        self.chunk_size = chunk_size

    def download_meta_file(self, backup):
        """
        :type backup: freezer.storage.Backup
        :param backup:
        :return:
        """
        utils.create_dir(self.work_dir)
        if backup.level == 0:
            return utils.path_join(self.work_dir, backup.tar())
        meta_backup = backup.full_backup.increments[backup.level - 1]
        zero_backup = self._zero_backup_dir(backup)
        to_path = utils.path_join(self.work_dir, meta_backup.tar())
        if os.path.exists(to_path):
            os.remove(to_path)
        from_path = utils.path_join(zero_backup, meta_backup.tar())
        shutil.copyfile(from_path, to_path)
        return to_path

    def upload_meta_file(self, backup, meta_file):
        zero_backup = self._zero_backup_dir(backup)
        to_path = utils.path_join(zero_backup, backup.tar())
        shutil.copyfile(meta_file, to_path)

    def prepare(self):
        utils.create_dir(self.storage_directory)

    def get_backups(self):
        backup_names = os.listdir(self.storage_directory)
        logging.info(backup_names)
        backups = []
        for backup_name in backup_names:
            backup_dir = utils.path_join(self.storage_directory, backup_name)
            timestamps = os.listdir(backup_dir)
            for timestamp in timestamps:
                increments = \
                    os.listdir(utils.path_join(backup_dir, timestamp))
                backups.extend(storage.Backup.parse_backups(increments))
        logging.info(backups)
        return backups

    def info(self):
        pass

    def backup_to_file_path(self, backup):
        return utils.path_join(self._zero_backup_dir(backup), backup)

    def _zero_backup_dir(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.Backup
        :return:
        """
        return utils.path_join(self.storage_directory,
                               backup.hostname_backup_name,
                               backup.full_backup.timestamp)

    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.Backup
        :return:
        """
        shutil.rmtree(self._zero_backup_dir(backup))

    def backup_blocks(self, backup):
        filename = self.backup_to_file_path(backup)
        with io.open(filename, 'rb') as backup_file:
            while True:
                chunk = backup_file.read(self.chunk_size)
                if chunk == '':
                    break
                if len(chunk):
                    yield chunk

    def write_backup(self, rich_queue, backup):
        """
        Upload object on the remote swift server
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: SwiftBackup
        """
        filename = self.backup_to_file_path(backup)
        logging.info("Local storage write backup enter")
        if backup.level == 0:
            os.makedirs(os.path.dirname(filename))
        with io.open(filename, 'wb', buffering=self.chunk_size) as b_file:
            for message in rich_queue.get_messages():
                b_file.write(message)
        logging.info("Local storage write backup successfully finished")
