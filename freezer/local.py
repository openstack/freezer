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

import subprocess
import logging
import os
import shutil

from freezer import storage
from freezer import utils


class LocalStorage(storage.Storage):

    def prepare(self):
        utils.create_dir(self.storage_directory)

    def get_backups(self):
        backup_names = os.listdir(self.storage_directory)
        backups = []
        for backup_name in backup_names:
            backup_dir = self.storage_directory + "/" + backup_name
            timestamps = os.listdir(backup_dir)
            for timestamp in timestamps:
                increments = os.listdir(backup_dir + "/" + timestamp)
                backups.extend(self._get_backups(increments))
        return backups

    def __init__(self, storage_directory):
        """
        :param storage_directory: directory of storage
        :type storage_directory: str
        :return:
        """
        self.storage_directory = storage_directory

    def info(self):
        pass

    def _backup_dir(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.Backup
        :return:
        """
        return "{0}/{1}".format(self.storage_directory,
                                backup.hostname_backup_name)

    def _zero_backup_dir(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.Backup
        :return:
        """
        return "{0}/{1}".format(self._backup_dir(backup), backup.timestamp)

    def backup(self, path, hostname_backup_name, tar_builder,
               parent_backup=None):
        """
        Backup path
        storage_dir/backup_name/timestamp/backup_name_timestamps_level
        :param path:
        :param hostname_backup_name:
        :param tar_builder:
        :type tar_builder: freezer.tar.TarCommandBuilder
        :param parent_backup:
        :type parent_backup: freezer.storage.Backup
        :return:
        """
        new_backup = self._create_backup(hostname_backup_name, parent_backup)

        host_backups = self._backup_dir(new_backup)
        utils.create_dir(host_backups)

        if parent_backup:
            zero_backup = self._zero_backup_dir(parent_backup.parent)
        else:
            zero_backup = self._zero_backup_dir(new_backup)
        utils.create_dir(zero_backup)
        tar_builder.set_output_file("{0}/{1}".format(zero_backup,
                                                     new_backup.repr()))

        tar_incremental = "{0}/{1}".format(zero_backup, new_backup.tar())
        if parent_backup:
            shutil.copyfile("{0}/{1}".format(
                zero_backup, parent_backup.tar()), tar_incremental)

        tar_builder.set_listed_incremental(tar_incremental)

        logging.info('[*] Changing current working directory to: {0}'
                     .format(path))
        logging.info('[*] Backup started for: {0}'.format(path))

        subprocess.check_output(tar_builder.build(), shell=True)

    def is_ready(self):
        return os.path.isdir(self.storage_directory)

    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.Backup
        :return:
        """
        shutil.rmtree(self._zero_backup_dir(backup))

    def restore(self, backup, path, tar_builder):
        """
        :param backup:
        :type backup: freezer.storage.Backup
        :param path:
        :param tar_builder:
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        :return:
        """
        zero_dir = self._zero_backup_dir(backup.parent)
        for level in range(0, backup.level + 1):
            c_backup = backup.parent.increments[level]
            tar_builder.set_archive(zero_dir + "/" + c_backup.repr())
            subprocess.check_output(tar_builder.build(), shell=True)
