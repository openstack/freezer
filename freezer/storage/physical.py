"""
(c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.

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

import abc
import os

import six

from freezer.storage import base
from freezer.utils import utils


@six.add_metaclass(abc.ABCMeta)
class PhysicalStorage(base.Storage):
    """
    Backup like Swift, SSH or Local. Something that represents real storage.
    For example MultipleStorage is not physical.
    """

    def __init__(self, storage_path, max_segment_size,
                 skip_prepare=False):
        self.storage_path = storage_path
        self.max_segment_size = max_segment_size
        super(PhysicalStorage, self).__init__(skip_prepare=skip_prepare)

    def metadata_path(self, engine, hostname_backup_name):
        return utils.path_join(self.storage_path, "metadata", engine.name,
                               hostname_backup_name)

    def get_level_zero(self,
                       engine,
                       hostname_backup_name,
                       recent_to_date=None):
        """
        Gets backups by backup_name and hostname

        :type engine: freezer.engine.engine.BackupEngine
        :param engine: Search for backups made by specified engine
        :type hostname_backup_name: str
        :param hostname_backup_name: Search for backup with specified name
        :type recent_to_date: int
        :param recent_to_date:
        :rtype: list[freezer.storage.base.Backup]
        :return: dictionary of level zero timestamps with attached storage
        """

        path = self.metadata_path(
            engine=engine,
            hostname_backup_name=hostname_backup_name)

        zeros = [base.Backup(
            storage=self,
            engine=engine,
            hostname_backup_name=hostname_backup_name,
            level_zero_timestamp=int(t),
            timestamp=int(t),
            level=0) for t in self.listdir(path)]
        if recent_to_date:
            zeros = [zero for zero in zeros
                     if zero.timestamp <= recent_to_date]
        return zeros

    @abc.abstractmethod
    def backup_blocks(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        pass

    @abc.abstractmethod
    def listdir(self, path):
        """
        :type path: str
        :param path:
        :rtype: collections.Iterable[str]
        """
        pass

    def put_metadata(self,
                     engine_metadata_path,
                     freezer_metadata_path,
                     backup):
        """
        :param engine_metadata_path:
        :param freezer_metadata_path:
        :type backup: freezer.storage.base.Backup
        :param backup:
        :return:
        """
        backup = backup.copy(self)
        self.put_file(engine_metadata_path, backup.engine_metadata_path)
        self.create_dirs(os.path.dirname(backup.metadata_path))
        self.put_file(freezer_metadata_path, backup.metadata_path)

    @abc.abstractmethod
    def rmtree(self, path):
        pass
