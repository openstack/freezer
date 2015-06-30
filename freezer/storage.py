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

import re
import utils
import logging


class Storage(object):
    """
    Any freezer storage implementation should be inherited from this abstract
    class.
    """

    def is_ready(self):
        """

        :rtype: bool
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def prepare(self):
        """

        :return: nothing
        """
        raise NotImplementedError("Should have implemented this")

    def find(self, hostname_backup_name):
        """
        Gets backups my backup_name and hostname
        :param hostname_backup_name:
        :rtype: list[Backup]
        :return: List of matched backups
        """
        return [b for b in self.get_backups()
                if b.hostname_backup_name == hostname_backup_name]

    def get_backups(self):
        raise NotImplementedError("Should have implemented this")

    def backup(self, path, hostname_backup_name, tar_builder,
               parent_backup=None):
        """
        Implements backup of path directory.

        :type path: str
        :type hostname_backup_name: str
        :type tar_builder: freezer.tar.TarCommandBuilder
        :param parent_backup: Can be None.
                Previous backup for incremental update.
        :type parent_backup: Backup
        """
        raise NotImplementedError("Should have implemented this")

    def restore(self, backup, path, tar_builder, level):
        """

        :param backup:
        :param path:
        :param tar_builder:
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        :param level:
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def restore_from_date(self, hostname_backup_name,
                          path, tar_builder, restore_timestamp=None):
        """
        :param hostname_backup_name:
        :type hostname_backup_name: str
        :param restore_timestamp:
        :type restore_timestamp: int
        :param path:
        :type path: str
        :param tar_builder:
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        :return:
        """
        backups = self.find(hostname_backup_name)
        if not backups:
            raise Exception("[*] No backups found")
        level = 0
        if restore_timestamp:
            backups = [b for b in backups
                       if b.timestamp <= restore_timestamp and b.tar_meta]
            backup = min(backups, key=lambda b: b.timestamp)
            if not backup:
                raise ValueError('No matching backup name {0} found'
                                 .format(hostname_backup_name))
            while (level in backup.increments
                   and backup.increments[level].timestamp
                    <= restore_timestamp):
                level += 1

            if level in backup.increments \
                    and backup.increments[level].timestamp > restore_timestamp:
                level -= 1
        else:
            backup = max(backups, key=lambda b: b.timestamp)
            if not backup:
                raise ValueError('No matching backup name {0} found'
                                 .format(hostname_backup_name))
            level = backup.latest_update.level

        self.restore(backup, path, tar_builder, level)

    def remove_older_than(self, remove_older_timestamp, hostname_backup_name):
        raise NotImplementedError("Should have implemented this")

    def info(self):
        raise NotImplementedError("Should have implemented this")

    @staticmethod
    def _create_backup(name, backup=None):
        """
        :param name:
        :type name: str
        :param backup:
        :type backup: Backup
        :rtype: Backup
        :return:
        """
        return Backup(name, utils.DateTime.now().timestamp,
                      backup.latest_update.level + 1 if backup else 0)

    @staticmethod
    def _get_backups(names):
        """
        No side effect version of get_backups
        :param names:
        :type names: list[str]
        :rtype: list[Backup]
        :return: list of zero level backups
        """
        prefix = 'tar_metadata_'
        tar_names = set([x[len(prefix):]
                         for x in names if x.startswith(prefix)])
        backup_names = [x for x in names if not x.startswith(prefix)]
        backups = []
        """:type: list[Backup]"""
        for name in backup_names:
            try:
                backup = Backup.parse(name)
                backup.tar_meta = name in tar_names
                backups.append(backup)
            except Exception as e:
                logging.exception(e)
                logging.error("cannot parse swift backup name: {0}"
                              .format(name))
        backups.sort(key=lambda x: (x.timestamp, x.level))
        zero_backups = []
        last_backup = None

        """:type last_backup: freezer.storage.Backup"""
        for backup in backups:
            if backup.level == 0:
                zero_backups.append(backup)
                last_backup = backup
            else:
                last_backup.add_increment(backup)

        return zero_backups

    def find_previous_backup(self, hostname_backup_name, no_incremental,
                             max_level, always_level, restart_always_level):
        backups = self.find(hostname_backup_name)
        return self._find_previous_backup(backups, no_incremental, max_level,
                                          always_level, restart_always_level)

    @staticmethod
    def _find_previous_backup(backups, no_incremental, max_level, always_level,
                              restart_always_level):
        """

        :param backups:
        :type backups: list[Backup]
        :param no_incremental:
        :param max_level:
        :param always_level:
        :param restart_always_level:
        :return:
        """
        if no_incremental or not backups:
            return None
        incremental_backup = max(backups, key=lambda x: x.timestamp)
        """:type : freezer.storage.Backup"""
        latest_update = incremental_backup.latest_update
        if max_level and max_level <= latest_update.level:
            latest_update = None
        elif always_level and latest_update.level >= always_level:
            if latest_update.level > 0:
                latest_update = \
                    incremental_backup.increments[latest_update.level - 1]
            else:
                latest_update = None
        elif restart_always_level and utils.DateTime.now().timestamp > \
                latest_update.timestamp + restart_always_level * 86400:
            latest_update = None
        return latest_update


class Backup:
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

    def __init__(self, hostname_backup_name, timestamp, level, tar_meta=False):
        """

        :param hostname_backup_name: name (hostname_backup_name) of backup
        :type hostname_backup_name: str
        :param timestamp: timestamp of backup (when it was executed)
        :type timestamp: int
        :param level: level of backup (freezer supports incremental backup)
            Completed full backup has level 0 and can be restored without any
            additional information.
            Levels 1, 2, ... means that our backup is incremental and contains
            only smart portion of information (that was actually changed
            since the last backup)
        :type level: int
        :param tar_meta: Is backup has or has not an attached meta
        tar file in storage. Default = False
        :type tar_meta: bool
        :return:
        """
        if not isinstance(level, int):
            raise ValueError("Level should have type int")
        self.hostname_backup_name = hostname_backup_name
        self._timestamp = timestamp
        self.tar_meta = tar_meta
        self._level = level
        self._increments = {0: self}
        self._latest_update = self
        self._parent = self

    @property
    def parent(self):
        return self._parent

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
        return "tar_metadata_{0}".format(self.repr())

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
        increment._parent = self
        if (increment.level not in self._increments or
                increment.timestamp >
                self._increments[increment.level].timestamp):
            self._increments[increment.level] = increment
        if self.latest_update.level <= increment.level:
            self._latest_update = increment

    def repr(self):
        return '_'.join([self.hostname_backup_name,
                         repr(self._timestamp), repr(self._level)])

    @staticmethod
    def parse(value):
        """

        :param value:
        :type value: str
        :return:
        """
        match = re.search(Backup.PATTERN, value, re.I)
        if not match:
            raise ValueError("Cannot parse backup from string: " + value)
        return Backup(match.group(1), int(match.group(2)), int(match.group(3)))

    def __eq__(self, other):
        if self is other:
            return True
        return type(other) is type(self) and \
            self.hostname_backup_name == other.hostname_backup_name and \
            self._timestamp == other.timestamp and \
            self.tar_meta == other.tar_meta and \
            self._level == other.level and \
            len(self.increments) == len(other.increments)
