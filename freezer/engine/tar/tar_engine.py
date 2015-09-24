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
========================================================================

Freezer general utils functions
"""
import logging
import os
import subprocess
import sys
import threading

from freezer.engine import engine
from freezer.engine.tar import tar_builders
from freezer import streaming
from freezer import winutils


class TarBackupEngine(engine.BackupEngine):
    DEFAULT_CHUNK_SIZE = 20000000

    def __init__(
            self, compression_algo, dereference_symlink, exclude, main_storage,
            is_windows, encrypt_pass_file=None, dry_run=False,
            chunk_size=DEFAULT_CHUNK_SIZE):
        self.compression_algo = compression_algo
        self.encrypt_pass_file = encrypt_pass_file
        self.dereference_symlink = dereference_symlink
        self.exclude = exclude
        self._main_storage = main_storage
        self.is_windows = is_windows
        self.dry_run = dry_run
        self.chunk_size = chunk_size

    @property
    def main_storage(self):
        """
        :rtype: freezer.storage.Storage
        :return:
        """
        return self._main_storage

    @staticmethod
    def reader(rich_queue, read_pipe, size=DEFAULT_CHUNK_SIZE):
        """
        :param rich_queue:
        :type rich_queue: freezer.streaming.RichQueue
        :type
        :return:
        """
        while True:
            tar_chunk = read_pipe.read(size)
            if tar_chunk == '':
                break
            if tar_chunk:
                rich_queue.put(tar_chunk)
        rich_queue.finish()

    @staticmethod
    def writer(rich_queue, write_pipe):
        """
        :param rich_queue:
        :type rich_queue: freezer.streaming.RichQueue
        :type
        :return:
        """
        for message in rich_queue.get_messages():
            logging.debug("Write next chunk to tar stdin")
            write_pipe.write(message)

    def post_backup(self, backup, manifest):
        self.main_storage.upload_meta_file(backup, manifest)

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

        tar_queue = streaming.RichQueue()
        tar_process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)

        reader = threading.Thread(target=self.reader,
                                  args=(tar_queue, tar_process.stdout))
        reader.daemon = True
        reader.start()
        while tar_queue.has_more():
            try:
                yield tar_queue.get()
            except streaming.Wait:
                pass
        logging.info("Tar engine streaming end")

    def restore_level(self, restore_path, read_pipe):
        """
        Restore the provided file into backup_opt_dict.restore_abs_path
        Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided
        """

        tar_command = tar_builders.TarCommandRestoreBuilder(
            restore_path, self.compression_algo, self.is_windows)

        if self.encrypt_pass_file:
            tar_command.set_encryption(self.encrypt_pass_file)

        if self.dry_run:
            tar_command.set_dry_run()

        command = tar_command.build()

        if winutils.is_windows():
            # on windows, chdir to restore path.
            os.chdir(restore_path)

        tar_cmd_proc = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=True)
        # Start loop reading the pipe and pass the data to the tar std input.
        # If EOFError exception is raised, the loop end the std err will be
        # checked for errors.
        try:
            while True:
                t = read_pipe.recv_bytes()
                tar_cmd_proc.stdin.write(t)
        except EOFError:
            logging.info('[*] Pipe closed as EOF reached. '
                         'Data transmitted successfully')

        tar_err = tar_cmd_proc.communicate()[1]

        if 'error' in tar_err.lower():
            logging.exception('[*] Restore error: {0}'.format(tar_err))
            sys.exit(1)
