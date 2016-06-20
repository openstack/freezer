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
import os
import re
import six

from oslo_log import log

from freezer.utils import utils

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Storage(object):
    """
    Any freezer storage implementation should be inherited from this abstract
    class.
    """

    def __init__(self, work_dir, skip_prepare=False):
        self.work_dir = work_dir
        if not skip_prepare:
            self.prepare()

    def download_meta_file(self, backup):
        """
        Downloads meta_data to work_dir of previous backup.
        :type backup: freezer.storage.base.Backup
        :param backup: A backup or increment. Current backup is incremental,
        that means we should download tar_meta for detection new files and
        changes. If backup.tar_meta is false, raise Exception
        :return:
        """
        utils.create_dir(self.work_dir)
        if backup.level == 0:
            return utils.path_join(self.work_dir, backup.tar())
        meta_backup = backup.full_backup.increments[backup.level - 1]
        if not meta_backup.tar_meta:
            raise ValueError('Latest update have no tar_meta')
        to_path = utils.path_join(self.work_dir, meta_backup.tar())
        if os.path.exists(to_path):
            os.remove(to_path)
        meta_backup.storage.get_file(
            meta_backup.storage.meta_file_abs_path(meta_backup), to_path)
        return to_path

    @abc.abstractmethod
    def meta_file_abs_path(self, backup):
        pass

    @abc.abstractmethod
    def get_file(self, from_path, to_path):
        pass

    @abc.abstractmethod
    def upload_meta_file(self, backup, meta_file):
        """
        :param backup:
        :type backup: freezer.storage.base.Backup
        :param meta_file:
        :return:
        """
        pass

    @abc.abstractmethod
    def upload_freezer_meta_data(self, backup, meta_dict):
        pass

    @abc.abstractmethod
    def download_freezer_meta_data(self, backup):
        pass

    @abc.abstractmethod
    def backup_blocks(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
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

    def find_one(self, hostname_backup_name, recent_to_date=None):
        """
        :param hostname_backup_name:
        :type hostname_backup_name: str
        :param recent_to_date:
        :type recent_to_date: int
        :rtype: Backup
        :return:
        """
        backups = self.find_all(hostname_backup_name)
        if recent_to_date:
            backups = [b for b in backups
                       if b.timestamp <= recent_to_date]
        err_msg = 'No matching backup name "{0}" found'\
            .format(hostname_backup_name)
        if not backups:
            raise IndexError(err_msg)
        backup = max(backups, key=lambda b: b.timestamp)
        last_increments = backup.increments.values()
        if recent_to_date:
            last_increments = [x for x in last_increments
                               if x.timestamp <= recent_to_date]
        return max(last_increments, key=lambda x: x.timestamp)

    @abc.abstractmethod
    def find_all(self, hostname_backup_name):
        """
        Gets backups by backup_name and hostname
        :param hostname_backup_name:
        :type hostname_backup_name: str
        :rtype: list[freezer.storage.base.Backup]
        :return: List of matched backups
        """
        pass

    @abc.abstractmethod
    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.base.Backup
        :param backup:
        :return:
        """
        pass

    def remove_older_than(self, remove_older_timestamp, hostname_backup_name):
        """
        Removes backups which are older than the specified timestamp
        :type remove_older_timestamp: int
        :type hostname_backup_name: str
        """
        backups = self.find_all(hostname_backup_name)
        backups = [b for b in backups
                   if b.latest_update.timestamp < remove_older_timestamp]
        for b in backups:
            b.storage.remove_backup(b)

    @abc.abstractmethod
    def info(self):
        pass

    def create_backup(self, hostname_backup_name, no_incremental,
                      max_level, always_level, restart_always_level,
                      time_stamp=None):
        backups = self.find_all(hostname_backup_name)
        prev_backup = self._find_previous_backup(
            backups, no_incremental, max_level, always_level,
            restart_always_level)
        time_stamp = time_stamp or utils.DateTime.now().timestamp
        if prev_backup and prev_backup.tar_meta:
            return Backup(
                self, hostname_backup_name, time_stamp,
                prev_backup.level + 1, prev_backup.full_backup)
        else:
            return Backup(
                self, hostname_backup_name, time_stamp)

    @staticmethod
    def _find_previous_backup(backups, no_incremental, max_level, always_level,
                              restart_always_level):
        """

        :param backups:
        :type backups: list[freezer.storage.base.Backup]
        :param no_incremental:
        :param max_level:
        :param always_level:
        :param restart_always_level:
        :rtype: freezer.storage.base.Backup
        :return:
        """
        if no_incremental or not backups:
            return None
        incremental_backup = max(backups, key=lambda x: x.timestamp)
        """:type : freezer.storage.base.Backup"""
        latest_update = incremental_backup.latest_update
        if max_level and max_level <= latest_update.level:
            return None
        elif always_level and latest_update.level >= always_level:
                latest_update = \
                    incremental_backup.increments[latest_update.level - 1]
        elif restart_always_level and utils.DateTime.now().timestamp > \
                latest_update.timestamp + restart_always_level * 86400:
            return None
        return latest_update


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
        tar_meta - boolean value, that is true when we have available meta
        information.
        Please check for additional information about tar_meta
            http://www.gnu.org/software/tar/manual/html_node/Incremental-Dumps.html
    """
    PATTERN = r'(.*)_(\d+)_(\d+?)$'

    def __init__(self, storage, hostname_backup_name, timestamp, level=0,
                 full_backup=None, tar_meta=False):
        """
        :type storage: freezer.storage.base.Storage
        :param hostname_backup_name: name (hostname_backup_name) of backup
        :type hostname_backup_name: str
        :param timestamp: timestamp of backup (when it was executed)
        :type timestamp: int
        :param full_backup: Previous full_backup - not increment
        :type full_backup: Backup
        :param level: current incremental level of backup
        :type level: int
        :param tar_meta: Is backup has or has not an attached meta
        tar file in storage. Default = False
        :type tar_meta: bool
        :return:
        """
        if level == 0 and full_backup:
            raise ValueError("Detected incremental backup without level")
        self.hostname_backup_name = hostname_backup_name
        self._timestamp = timestamp
        self.tar_meta = tar_meta
        self._increments = {0: self}
        self._latest_update = self
        self._level = level
        self.storage = storage
        if not full_backup:
            self._full_backup = self
        else:
            self._full_backup = full_backup

    @property
    def full_backup(self):
        return self._full_backup

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def level(self):
        return self._level

    @property
    def increments(self):
        return self._increments

    @property
    def latest_update(self):
        return self._latest_update

    def tar(self):
        return "tar_metadata_{0}".format(self)

    def metadata(self):
        return self.storage.download_freezer_meta_data(self)

    def add_increment(self, increment):
        """

        :param increment:
        :type increment: Backup
        :return:
        """
        if self.level != 0:
            raise ValueError("Can not add increment to increment")
        if increment.level == 0:
            raise ValueError("Can not add increment with level 0")
        if (increment.level not in self._increments or
                increment.timestamp >
                self._increments[increment.level].timestamp):
            self._increments[increment.level] = increment
        if self.latest_update.level <= increment.level:
            self._latest_update = increment

    def __repr__(self):
        return '_'.join([self.hostname_backup_name,
                         repr(self._timestamp), repr(self._level)])

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_backups(names, storage):
        """
        :param names:
        :type names: list[str] - file names of backups.
        :type storage: freezer.storage.base.Storage
        File name should be something like that host_backup_timestamp_level
        :rtype: list[freezer.storage.base.Backup]
        :return: list of zero level backups
        """
        prefix = 'tar_metadata_'
        tar_names = set([x[len(prefix):]
                         for x in names if x.startswith(prefix)])
        backup_names = [x for x in names if not x.startswith(prefix)]
        backups = []
        """:type: list[freezer.storage.base.BackupRepr]"""
        for name in backup_names:
            try:
                backup = Backup._parse(name)
                backup.tar_meta = name in tar_names
                backups.append(backup)
            except Exception as e:
                LOG.exception(e)
                LOG.error("cannot parse backup name: {0}".format(name))
        backups.sort(
            key=lambda x: (x.hostname_backup_name, x.timestamp, x.level))
        zero_backups = []
        """:type: list[freezer.storage.base.Backup]"""
        last_backup = None

        """:type last_backup: freezer.storage.base.Backup"""
        for backup in backups:
            if backup.level == 0:
                last_backup = backup.backup(storage)
                zero_backups.append(last_backup)
            else:
                if last_backup:
                    last_backup.add_increment(backup.backup(storage,
                                                            last_backup))
                else:
                    LOG.error("Incremental backup without parent: {0}"
                              .format(backup))

        return zero_backups

    @staticmethod
    def _parse(value):
        """
        :param value: String representation of backup
        :type value: str
        :return:
        """
        match = re.search(Backup.PATTERN, value, re.I)
        if not match:
            raise ValueError("Cannot parse backup from string: " + value)
        return BackupRepr(match.group(1), int(match.group(2)),
                          int(match.group(3)))

    def __eq__(self, other):
        if self is other:
            return True
        return type(other) is type(self) and \
            self.hostname_backup_name == other.hostname_backup_name and \
            self._timestamp == other.timestamp and \
            self.tar_meta == other.tar_meta and \
            self._level == other.level and \
            len(self.increments) == len(other.increments)


class BackupRepr(object):
    """
    Intermediate for parsing purposes - it parsed backup name.
    Difference between Backup and BackupRepr - backupRepr can be parsed from
    str and doesn't require information about full_backup
    """
    def __init__(self, hostname_backup_name, timestamp, level, tar_meta=False):
        """

        :param hostname_backup_name:
        :type hostname_backup_name: str
        :param timestamp:
        :type timestamp: int
        :param level:
        :type level: int
        :param tar_meta:
        :type tar_meta: bool
        :return:
        """
        self.hostname_backup_name = hostname_backup_name
        self.timestamp = timestamp
        self.level = level
        self.tar_meta = tar_meta

    def backup(self, storage, full_backup=None):
        """

        :param storage:
        :type storage: freezer.storage.base.Storage
        :param full_backup: freezer.storage.base.Backup
        :return:
        """
        return Backup(storage, self.hostname_backup_name, self.timestamp,
                      level=self.level, full_backup=full_backup,
                      tar_meta=self.tar_meta)
