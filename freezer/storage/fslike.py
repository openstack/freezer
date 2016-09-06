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

from freezer.storage import physical


@six.add_metaclass(abc.ABCMeta)
class FsLikeStorage(physical.PhysicalStorage):
    def __init__(self, storage_path,
                 max_segment_size, skip_prepare=False):
        super(FsLikeStorage, self).__init__(
            storage_path=storage_path,
            max_segment_size=max_segment_size,
            skip_prepare=skip_prepare)

    def prepare(self):
        self.create_dirs(self.storage_path)

    def info(self):
        pass

    def write_backup(self, rich_queue, backup):
        """
        Stores backup in storage
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        backup = backup.copy(storage=self)
        path = backup.data_path
        self.create_dirs(path.rsplit('/', 1)[0])

        with self.open(path, mode='wb') as \
                b_file:
            for message in rich_queue.get_messages():
                b_file.write(message)

    def backup_blocks(self, backup):
        """

        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        with self.open(backup.data_path, 'rb') as backup_file:
            while True:
                chunk = backup_file.read(self.max_segment_size)
                if chunk == '':
                    break
                if len(chunk):
                    yield chunk

    @abc.abstractmethod
    def open(self, filename, mode):
        """
        :type filename: str
        :param filename:
        :type mode: str
        :param mode:
        :return:
        """
        pass
