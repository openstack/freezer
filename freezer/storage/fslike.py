# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import six

from oslo_log import log

from freezer.storage import base
from freezer.utils import utils

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class FsLikeStorage(base.Storage):
    DEFAULT_CHUNK_SIZE = 10000000

    def __init__(self, storage_directory, work_dir,
                 chunk_size=DEFAULT_CHUNK_SIZE, skip_prepare=False):
        self.storage_directory = storage_directory
        self.chunk_size = chunk_size
        super(FsLikeStorage, self).__init__(work_dir,
                                            skip_prepare=skip_prepare)

    def backup_to_file_path(self, backup):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        return utils.path_join(self._zero_backup_dir(backup), backup)

    def _zero_backup_dir(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        return utils.path_join(self.storage_directory,
                               backup.hostname_backup_name,
                               backup.full_backup.timestamp)

    def prepare(self):
        self.create_dirs(self.storage_directory)

    def info(self):
        pass

    def meta_file_abs_path(self, backup):
        zero_backup = self._zero_backup_dir(backup)
        return utils.path_join(zero_backup, backup.tar())

    def upload_meta_file(self, backup, meta_file):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :param meta_file:
        :return:
        """
        zero_backup = self._zero_backup_dir(backup)
        to_path = utils.path_join(zero_backup, backup.tar())
        self.put_file(meta_file, to_path)

    def find_all(self, hostname_backup_name):
        backups = []
        backup_dir = utils.path_join(self.storage_directory,
                                     hostname_backup_name)
        self.create_dirs(backup_dir)
        timestamps = self.listdir(backup_dir)
        for timestamp in timestamps:
            increments = \
                self.listdir(utils.path_join(backup_dir, timestamp))
            backups.extend(base.Backup.parse_backups(increments, self))
        return backups

    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.base.Backup
        :return:
        """
        self.rmtree(self._zero_backup_dir(backup))

    def write_backup(self, rich_queue, backup):
        """
        Stores backup in storage
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        filename = self.backup_to_file_path(backup)
        if backup.level == 0:
            self.create_dirs(self._zero_backup_dir(backup))

        with self.open(filename, mode='wb') as b_file:
            for message in rich_queue.get_messages():
                b_file.write(message)

    def backup_blocks(self, backup):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        filename = self.backup_to_file_path(backup)
        with self.open(filename, 'rb') as backup_file:
            while True:
                chunk = backup_file.read(self.chunk_size)
                if chunk == '':
                    break
                if len(chunk):
                    yield chunk

    @abc.abstractmethod
    def listdir(self, directory):
        pass

    @abc.abstractmethod
    def put_file(self, from_path, to_path):
        pass

    @abc.abstractmethod
    def create_dirs(self, path):
        pass

    @abc.abstractmethod
    def rmtree(self, path):
        pass

    @abc.abstractmethod
    def open(self, filename, mode):
        pass

    def download_freezer_meta_data(self, backup):
        return {}

    def upload_freezer_meta_data(self, backup, meta_dict):
        pass
