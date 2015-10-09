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
import stat
import logging

import paramiko

from freezer.storage import storage
from freezer import utils


class SshStorage(storage.Storage):
    """
    :type ftp: paramiko.SFTPClient
    """
    DEFAULT_CHUNK_SIZE = 10000000

    def __init__(self, storage_directory, work_dir,
                 ssh_key_path, remote_username, remote_ip,
                 port, chunk_size=DEFAULT_CHUNK_SIZE):
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
        self.chunk_size = chunk_size
        self.port = port
        # automatically add keys without requiring human intervention
        self.ssh = None
        self.ftp = None
        self.init()

    def init(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(self.remote_ip, username=self.remote_username,
                    key_filename=self.ssh_key_path, port=self.port)

        # we should keep link to ssh to prevent garbage collection
        self.ssh = ssh
        self.ftp = self.ssh.open_sftp()

    def prepare(self):
        self.mkdir_p(self.storage_directory)

    def get_backups(self):
        backup_names = self.ftp.listdir(self.storage_directory)
        backups = []
        for backup_name in backup_names:
            backup_dir = utils.path_join(self.storage_directory, backup_name)
            timestamps = self.ftp.listdir(backup_dir)
            for timestamp in timestamps:
                increments = self.ftp.listdir(
                    utils.path_join(backup_dir, timestamp))
                backups.extend(storage.Backup.parse_backups(increments))
        return backups

    def info(self):
        pass

    def backup_dir(self, backup):
        return utils.path_join(self._zero_backup_dir(backup), backup)

    def _zero_backup_dir(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.Backup
        :return:
        """
        return utils.path_join(
            self.storage_directory, backup.hostname_backup_name,
            backup.full_backup.timestamp)

    def _is_dir(self, check_dir):
        return stat.S_IFMT(self.ftp.stat(check_dir).st_mode) == stat.S_IFDIR

    def _rm(self, path):
        files = self.ftp.listdir(path=path)
        for f in files:
            filepath = utils.path_join(path, f)
            if self._is_dir(filepath):
                self._rm(filepath)
            else:
                self.ftp.remove(filepath)
        self.ftp.rmdir(path)

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
        from_path = utils.path_join(zero_backup, meta_backup.tar())
        to_path = utils.path_join(self.work_dir, meta_backup.tar())
        if backup.level != 0:
            if os.path.exists(to_path):
                os.remove(to_path)
            self.ftp.get(from_path, to_path)
        return to_path

    def upload_meta_file(self, backup, meta_file):
        zero_backup = self._zero_backup_dir(backup)
        to_path = utils.path_join(zero_backup, backup.tar())
        logging.info("Ssh storage uploading {0} to {1}".format(meta_file,
                                                               to_path))
        self.ftp.put(meta_file, to_path)

    def remove_backup(self, backup):
        """
        :type backup: freezer.storage.Backup
        :return:
        """
        self._rm(self._zero_backup_dir(backup))

    def backup_blocks(self, backup):
        self.init()
        filename = self.backup_dir(backup)
        with self.ftp.open(filename, mode='rb') as backup_file:
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
        filename = self.backup_dir(backup)
        self.mkdir_p(self._zero_backup_dir(backup))
        logging.info("SSH write backup enter")

        with self.ftp.open(filename, mode='wb',
                           bufsize=self.chunk_size) as b_file:
            logging.debug("SSH write backup getting chunk")
            for message in rich_queue.get_messages():
                b_file.write(message)
