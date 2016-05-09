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

Freezer general utils functions
"""
import logging
import os
import subprocess
import sys

from freezer.engine import engine
from freezer.engine.tar import tar_builders
from freezer.utils import winutils


class TarBackupEngine(engine.BackupEngine):

    def __init__(
            self, compression_algo, dereference_symlink, exclude, storage,
            is_windows, chunk_size, encrypt_pass_file=None, dry_run=False):
        """
            :type storage: freezer.storage.base.Storage
        :return:
        """
        self.compression_algo = compression_algo
        self.encrypt_pass_file = encrypt_pass_file
        self.dereference_symlink = dereference_symlink
        self.exclude = exclude
        self.storage = storage
        self.is_windows = is_windows
        self.dry_run = dry_run
        self.chunk_size = chunk_size

    def post_backup(self, backup, manifest):
        self.storage.upload_meta_file(backup, manifest)
        metadata = {
            "engine": "tar",
            "compression": self.compression_algo,
            "encryption": self.encrypt_pass_file is not None
        }

        self.storage.upload_freezer_meta_data(backup, metadata)

    def backup_data(self, backup_path, manifest_path):
        logging.info("Tar engine backup stream enter")
        tar_command = tar_builders.TarCommandBuilder(
            backup_path, self.compression_algo, self.is_windows)
        if self.encrypt_pass_file:
            tar_command.set_encryption(self.encrypt_pass_file)
        if self.dereference_symlink:
            tar_command.set_dereference(self.dereference_symlink)
        tar_command.set_exclude(self.exclude)
        tar_command.set_listed_incremental(manifest_path)

        command = tar_command.build()

        logging.info("Execution command: \n{}".format(command))

        tar_process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        read_pipe = tar_process.stdout
        tar_chunk = read_pipe.read(self.chunk_size)
        while tar_chunk:
            yield tar_chunk
            tar_chunk = read_pipe.read(self.chunk_size)
        tar_err = tar_process.communicate()[1]
        if 'error' in tar_err.lower():
            logging.exception('[*] Backup error: {0}'.format(tar_err))
            sys.exit(1)
        if tar_process.returncode:
            logging.error('[*] Backup return code is not 0')
            sys.exit(1)
        logging.info("Tar engine streaming end")

    @staticmethod
    def check_process_output(process):
        tar_err = process.communicate()[1]

        if 'error' in tar_err.lower():
            logging.exception('[*] Restore error: {0}'.format(tar_err))
            sys.exit(1)

        if process.returncode:
            logging.error('[*] Restore return code is not 0')
            sys.exit(1)

    def restore_level(self, restore_path, read_pipe, backup):
        """
        Restore the provided file into backup_opt_dict.restore_abs_path
        Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided
        """

        metadata = backup.metadata()
        if not self.encrypt_pass_file and metadata.get("encryption", False):
            raise Exception("Cannot restore encrypted backup without key")

        tar_command = tar_builders.TarCommandRestoreBuilder(
            restore_path,
            metadata.get('compression', self.compression_algo),
            self.is_windows)

        if self.encrypt_pass_file:
            tar_command.set_encryption(self.encrypt_pass_file)

        if self.dry_run:
            tar_command.set_dry_run()

        command = tar_command.build()

        if winutils.is_windows():
            # on windows, chdir to restore path.
            os.chdir(restore_path)

        tar_process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)
        # Start loop reading the pipe and pass the data to the tar std input.
        # If EOFError exception is raised, the loop end the std err will be
        # checked for errors.
        try:
            while True:
                tar_process.stdin.write(read_pipe.recv_bytes())
        except EOFError:
            logging.info('[*] Pipe closed as EOF reached. '
                         'Data transmitted successfully')

        self.check_process_output(tar_process)
