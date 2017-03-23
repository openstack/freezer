# (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.
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
import json
import tempfile

from oslo_log import log
import six

from freezer.utils import utils

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Storage(object):
    """
    Any freezer storage implementation should be inherited from this abstract
    class.
    """
    _type = None

    def __init__(self, skip_prepare=False):
        if not skip_prepare:
            self.prepare()

    @abc.abstractmethod
    def get_file(self, from_path, to_path):
        pass

    @abc.abstractmethod
    def write_backup(self, rich_queue, backup):
        """
        :param rich_queue:
        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        pass

    @abc.abstractmethod
    def prepare(self):
        """
        Creates directories, containers
        :return: nothing
        """
        pass

    @abc.abstractmethod
    def get_level_zero(self,
                       engine,
                       hostname_backup_name,
                       recent_to_date=None):
        """
        Gets backups by backup_name and hostname
        :type engine: freezer.engine.engine.BackupEngine
        :param hostname_backup_name:
        :type hostname_backup_name: str
        :type recent_to_date: int
        :param recent_to_date:
        :rtype: collections.Iterable[freezer.storage.base.Backup]
        :return: dictionary of level zero timestamps with attached storage
        """
        pass

    @property
    def type(self):
        return self._type

    def get_latest_level_zero_increments(self, engine, hostname_backup_name,
                                         recent_to_date=None):
        """
        Returns the latest zero level backup with increments
        :param engine:
        :param hostname_backup_name:
        :param recent_to_date:
        :rtype: dict[int, freezer.storage.base.Backup]
        :return: Dictionary[backup_level, backup]
        """
        zeros = self.get_level_zero(engine=engine,
                                    hostname_backup_name=hostname_backup_name,
                                    recent_to_date=recent_to_date)
        if not zeros:
            err_msg = 'No matching backup name "{0}" found'.format(
                hostname_backup_name
            )
            raise IndexError(err_msg)

        backup = max(zeros, key=lambda backup: backup.timestamp)
        """:type : freezer.storage.base.Backup"""

        increments = backup.get_increments()

        return {level: backup for level, backup in increments.iteritems()
                if not recent_to_date or backup.timestamp <= recent_to_date}

    def remove_older_than(self, engine, remove_older_timestamp,
                          hostname_backup_name):
        """
        Removes backups which are older than or equal to the specified
        timestamp
        :type engine: freezer.engine.engine.BackupEngine
        :type remove_older_timestamp: int
        :type hostname_backup_name: str
        """
        backups = self.get_level_zero(engine, hostname_backup_name,
                                      remove_older_timestamp)
        for backup in backups:
            backup.remove()

    @abc.abstractmethod
    def info(self):
        pass

    def previous_backup(self, engine, hostname_backup_name, no_incremental,
                        max_level, always_level, restart_always_level):
        """
        :type engine: freezer.engine.engine.BackupEngine
        :param engine: engine instance
        :param hostname_backup_name: name of backup
        :param no_incremental:
        :param max_level:
        :param always_level:
        :param restart_always_level:
        :return:
        """
        if no_incremental:
            return None
        try:
            increments = self.get_latest_level_zero_increments(
                engine=engine,
                hostname_backup_name=hostname_backup_name)
            highest_level = max(increments.keys())
            highest_level_backup = increments[highest_level]
            if max_level and max_level <= highest_level:
                return None
            if always_level and highest_level > always_level:
                return None
            expire_time = (highest_level_backup.timestamp +
                           restart_always_level * 86400)
            if restart_always_level and utils.DateTime.now().timestamp > \
                    expire_time:
                return None
            if always_level and highest_level == always_level:
                return increments[highest_level - 1]
            return highest_level_backup
        except IndexError:
            return None

    @abc.abstractmethod
    def put_file(self, from_path, to_path):
        """
        :type from_path: str
        :param from_path:
        :type to_path: str
        :param to_path:
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def create_dirs(self, path):
        pass


class Backup(object):
    """
    Internal freezer representation of backup.
    Includes:
        name (hostname_backup_name) of backup
        timestamp of backup (when it was executed)
        level of backup (freezer supports incremental backup)
            Completed full backup has level 0 and can be restored without any
            additional information.
            Levels 1, 2, ... means that our backup is incremental and contains
            only smart portion of information (that was actually changed
            since the last backup)
    """

    def __init__(self, engine, hostname_backup_name,
                 level_zero_timestamp, timestamp, level, storage=None):
        """
        :type storage: freezer.storage.physical.PhysicalStorage
        :param hostname_backup_name: name (hostname_backup_name) of backup
        :type hostname_backup_name: str
        :param timestamp: timestamp of backup (when it was executed)
        :type timestamp: int
        :param level: current incremental level of backup
        :type level: int
        :return:
        """
        self.hostname_backup_name = hostname_backup_name
        self.timestamp = timestamp
        self.level = level
        self.engine = engine
        self.storage = storage
        self.level_zero_timestamp = level_zero_timestamp
        if storage:
            self.increments_data_path = utils.path_join(
                self.storage.storage_path, "data", self.engine.name,
                self.hostname_backup_name, self.level_zero_timestamp)
            self.increments_metadata_path = utils.path_join(
                self.storage.storage_path, "metadata", self.engine.name,
                self.hostname_backup_name, self.level_zero_timestamp)
            self.data_prefix_path = utils.path_join(
                self.increments_data_path,
                "{0}_{1}".format(self.level, self.timestamp))
            self.engine_metadata_path = utils.path_join(
                self.data_prefix_path, "engine_metadata")
            self.metadata_path = utils.path_join(
                self.increments_metadata_path,
                "{0}_{1}".format(self.level, self.timestamp), "metadata")
            self.data_path = utils.path_join(self.data_prefix_path, "data")
            self.segments_path = utils.path_join(self.data_prefix_path,
                                                 "segments")

    def copy(self, storage):
        """
        :type storage: freezer.storage.physical.PhysicalStorage
        :return:
        """
        return Backup(
            engine=self.engine,
            hostname_backup_name=self.hostname_backup_name,
            level_zero_timestamp=self.level_zero_timestamp,
            timestamp=self.timestamp,
            level=self.level,
            storage=storage)

    def remove(self):
        self.storage.rmtree(self.increments_metadata_path)
        self.storage.rmtree(self.increments_data_path)

    def get_increments(self):
        """
        Gets all incremental backups based on a level-zero backup with
        timestamp
        :rtype: dict[int, freezer.storage.base.Backup]
        :return: Dictionary[backup_level, backup]
        """
        increments = self.storage.listdir(self.increments_metadata_path)
        sorted(increments)
        increments = [name.split('_') for name in increments]

        return {int(increment[0]): Backup(
            storage=self.storage,
            engine=self.engine,
            hostname_backup_name=self.hostname_backup_name,
            timestamp=int(increment[1]),
            level_zero_timestamp=self.level_zero_timestamp,
            level=int(increment[0])
        ) for increment in increments}

    def _get_file(self, filename):
        file = tempfile.NamedTemporaryFile('wb', delete=True)
        self.storage.get_file(filename, file.name)
        with open(file.name) as f:
            content = f.readlines()
        LOG.info("Content download {0}".format(content))
        file.close()
        return json.loads(content[0])

    def metadata(self):
        return self._get_file(self.metadata_path)

    def engine_metadata(self):
        return self._get_file(self.engine_metadata_path)
