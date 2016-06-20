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

"""

import os
import stat

import paramiko

from oslo_log import log

from freezer.storage import fslike

from freezer.utils import utils

LOG = log.getLogger(__name__)


class SshStorage(fslike.FsLikeStorage):
    """
    :type ftp: paramiko.SFTPClient
    """
    DEFAULT_CHUNK_SIZE = 10000000

    def __init__(self, storage_directory, work_dir, ssh_key_path,
                 remote_username, remote_ip, port,
                 chunk_size=DEFAULT_CHUNK_SIZE):
        """
            :param storage_directory: directory of storage
            :type storage_directory: str
            :return:
            """
        self.ssh_key_path = ssh_key_path
        self.remote_username = remote_username
        self.remote_ip = remote_ip
        self.port = port
        self.ssh = None
        self.ftp = None
        self.init()
        super(SshStorage, self).__init__(storage_directory, work_dir,
                                         chunk_size)

    def init(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(self.remote_ip, username=self.remote_username,
                    key_filename=self.ssh_key_path, port=self.port)

        # we should keep link to ssh to prevent garbage collection
        self.ssh = ssh
        self.ftp = self.ssh.open_sftp()

    def _is_dir(self, check_dir):
        return stat.S_IFMT(self.ftp.stat(check_dir).st_mode) == stat.S_IFDIR

    def rmtree(self, path):
        files = self.ftp.listdir(path=path)
        for f in files:
            filepath = utils.path_join(path, f)
            if self._is_dir(filepath):
                self.rmtree(filepath)
            else:
                self.ftp.remove(filepath)
        self.ftp.rmdir(path)

    def create_dirs(self, path):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if path == '/':
            # absolute path so change directory to root
            self.ftp.chdir('/')
            return
        if path == '':
            # top-level relative directory must exist
            return
        try:
            self.ftp.chdir(path)  # sub-directory exists
        except IOError:
            dirname, basename = os.path.split(path.rstrip('/'))
            self.create_dirs(dirname)  # make parent directories
            self.ftp.mkdir(basename)  # sub-directory missing, so created it
            self.ftp.chdir(basename)
            return True

    def get_file(self, from_path, to_path):
        self.ftp.get(from_path, to_path)

    def put_file(self, from_path, to_path):
        self.ftp.put(from_path, to_path)

    def listdir(self, directory):
        return self.ftp.listdir(directory)

    def open(self, filename, mode):
        return self.ftp.open(filename, mode=mode)

    def backup_blocks(self, backup):
        self.init()  # should recreate ssh for new process
        return super(SshStorage, self).backup_blocks(backup)
