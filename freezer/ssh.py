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
import stat
import paramiko


from freezer import storage


class SshStorage(storage.Storage):
    """
    :type ssh: paramiko.SSHClient
    :type ftp: paramiko.SFTPClient
    """
    def __init__(self, storage_directory, work_dir,
                 ssh_key_path, remote_username, remote_ip):
        """
        :param storage_directory: directory of storage
        :type storage_directory: str
        :return:
        """
        self.ssh_key_path = ssh_key_path
        self.remote_username = remote_username
        self.remote_ip = remote_ip
        self.storage_directory = storage_directory
        self.work_dir = work_dir
        ssh = paramiko.SSHClient()
        # automatically add keys without requiring human intervention
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(remote_ip, username=remote_username,
                    key_filename=ssh_key_path)
        self.ssh = ssh
        self.ftp = ssh.open_sftp()

    def prepare(self):
        if not self.is_ready():
            self.mkdir_p(self.storage_directory)

    def get_backups(self):
        backup_names = self.ftp.listdir(self.storage_directory)
        backups = []
        for backup_name in backup_names:
            backup_dir = self.storage_directory + "/" + backup_name
            timestamps = self.ftp.listdir(backup_dir)
            for timestamp in timestamps:
                increments = self.ftp.listdir(backup_dir + "/" + timestamp)
                backups.extend(self._get_backups(increments))
        return backups

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

        if parent_backup:
            zero_backup = self._zero_backup_dir(parent_backup.parent)
        else:
            zero_backup = self._zero_backup_dir(new_backup)
        self.mkdir_p(zero_backup)
        output_file = "{0}/{1}".format(zero_backup, new_backup.repr())
        tar_builder.set_output_file(output_file)
        tar_builder.set_ssh(self.ssh_key_path, self.remote_username,
                            self.remote_ip)
        tar_incremental = "{0}/{1}".format(self.work_dir, new_backup.tar())
        if parent_backup:
            self.ftp.get(zero_backup + "/" + parent_backup.tar(),
                         tar_incremental)

        tar_builder.set_listed_incremental(tar_incremental)

        logging.info('[*] Changing current working directory to: {0}'
                     .format(path))
        logging.info('[*] Backup started for: {0}'.format(path))

        subprocess.check_output(tar_builder.build(), shell=True)
        self.ftp.put(tar_incremental, zero_backup + "/" + new_backup.tar())

    def _is_dir(self, check_dir):
        return stat.S_IFMT(self.ftp.stat(check_dir).st_mode) == stat.S_IFDIR

    def rm(self, path):
        files = self.ftp.listdir(path=path)
        for f in files:
            filepath = os.path.join(path, f)
            if self._is_dir(filepath):
                self.rm(filepath)
            else:
                self.ftp.remove(filepath)
        self.ftp.rmdir(path)

    def is_ready(self):
        try:
            return self._is_dir(self.storage_directory)
        except IOError:
            return False

    def mkdir_p(self, remote_directory):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if remote_directory == '/':
            # absolute path so change directory to root
            self.ftp.chdir('/')
            return
        if remote_directory == '':
            # top-level relative directory must exist
            return
        try:
            self.ftp.chdir(remote_directory)  # sub-directory exists
        except IOError:
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            self.mkdir_p(dirname)  # make parent directories
            self.ftp.mkdir(basename)  # sub-directory missing, so created it
            self.ftp.chdir(basename)
            return True

    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.Backup
        :return:
        """
        self.rm(self._zero_backup_dir(backup))

    def restore(self, backup, path, tar_builder, level):
        """
        :param backup:
        :param path:
        :param tar_builder:
        :type tar_builder: freezer.tar.TarCommandRestoreBuilder
        :param level:
        :return:
        """
        zero_dir = self._zero_backup_dir(backup)
        for level in range(0, level + 1):
            c_backup = backup.increments[level]
            tar_builder.set_archive(zero_dir + "/" + c_backup.repr())
            tar_builder.set_ssh(self.ssh_key_path,
                                self.remote_username,
                                self.remote_ip)
            subprocess.check_output(tar_builder.build(), shell=True)
