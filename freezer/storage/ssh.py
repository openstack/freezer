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

import errno
import os
import stat

import paramiko

from freezer.storage import fslike
from freezer.utils import utils

CHUNK_SIZE = 32768


class SshStorage(fslike.FsLikeStorage):
    """
    :type ftp: paramiko.SFTPClient
    """
    _type = 'ssh'

    def __init__(self, storage_path, ssh_key_path,
                 remote_username, remote_ip, port, max_segment_size):
        """
            :param storage_path: directory of storage
            :type storage_path: str
            :return:
            """
        self.ssh_key_path = ssh_key_path
        self.remote_username = remote_username
        self.remote_ip = remote_ip
        self.port = port
        self.ssh = None
        self.ftp = None
        self._validate()
        self.init()
        super(SshStorage, self).__init__(
            storage_path=storage_path,
            max_segment_size=max_segment_size)

    def _validate(self):
        """
        Validates if all parameters required to ssh are available.
        :return: True or raises ValueError
        """
        if not self.remote_ip:
            raise ValueError('Please provide --ssh-host value.')
        elif not self.remote_username:
            raise ValueError('Please provide --ssh-username value.')
        elif not self.ssh_key_path:
            raise ValueError('Please provide path to ssh key using '
                             '--ssh-key argument.')
        return True

    def init(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
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
        if not self.ssh.get_transport().is_alive():
            self.init()
        self.ftp.get(from_path, to_path)

    def put_file(self, from_path, to_path):
        self.ftp.put(from_path, to_path)

    def listdir(self, directory):
        try:
            # paramiko SFTPClient.listdir_attr returns
            # directories in arbitarary order, so we should
            # sort results of this command
            res = self.ftp.listdir(directory)
            return sorted(res)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return list()
            else:
                raise

    def open(self, filename, mode):
        return self.ftp.open(filename, mode=mode,
                             bufsize=self.max_segment_size)

    def read_metadata_file(self, path):
        file_stats = self.ftp.stat(path)
        file_size = file_stats.st_size
        data = ""
        received_size = 0
        with self.open(path, 'r') as reader:
            reader.prefetch(file_size)
            chunk = reader.read(CHUNK_SIZE)
            while chunk:
                received_size += len(chunk)
                data += chunk
                chunk = reader.read(CHUNK_SIZE)
        if file_size != received_size:
            raise IOError('Size mismatch: expected {} received {}'.format(
                          file_size, received_size))
        return data

    def backup_blocks(self, backup):
        self.init()  # should recreate ssh for new process
        return super(SshStorage, self).backup_blocks(backup)
