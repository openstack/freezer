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
========================================================================

Freezer Tar related functions
"""

from freezer.utils import validate_all_args
from freezer.winutils import is_windows

import os
import logging
import subprocess
import sys


class TarCommandBuilder:
    """
    Building a tar cmd command. To build command invoke method build.
    """

    COMMAND_TEMPLATE = "{gnutar_path} --create -z --warning=none " \
        "--no-check-device --one-file-system --preserve-permissions " \
        "--same-owner --seek --ignore-failed-read"

    LISTED_TEMPLATE = "{tar_command} --listed-incremental={listed_incremental}"

    DEREFERENCE_MODE = {'soft': '--dereference',
                        'hard': '--hard-dereference',
                        'all': '--hard-dereference --dereference',
                        'none': ''}

    def __init__(self, gnutar_path, filepath):
        self.dereference = 'none'
        self.gnutar_path = gnutar_path
        self.exclude = None
        self.dereference = ''
        self.listed_incremental = None
        self.exclude = ''
        self.openssl_path = None
        self.encrypt_pass_file = None
        self.output_file = None
        self.filepath = filepath

    def set_output_file(self, output_file):
        self.output_file = output_file

    def set_listed_incremental(self, absolute_path):
        self.listed_incremental = absolute_path

    def set_exclude(self, exclude):
        self.exclude = exclude

    def set_dereference(self, mode):
        """
        Dereference hard and soft links according option choices.
            'soft' dereference soft links,
            'hard' dereference hardlinks,
            'all' dereference both.
            Default 'none'.
        """
        self.dereference = self.DEREFERENCE_MODE[mode]

    def set_encryption(self, openssl_path, encrypt_pass_file):
        self.openssl_path = openssl_path
        self.encrypt_pass_file = encrypt_pass_file

    def build(self):
        tar_command = self.COMMAND_TEMPLATE.format(
            gnutar_path=self.gnutar_path, dereference=self.dereference)
        if self.dereference:
            "{0} {1}".format(tar_command, self.dereference)
        if self.listed_incremental:
            tar_command = self.LISTED_TEMPLATE.format(
                tar_command=tar_command,
                listed_incremental=self.listed_incremental)

        if self.output_file:
            tar_command = "{0} --file={1}".format(tar_command,
                                                  self.output_file)

        if self.exclude:
            tar_command = '{tar_command} --exclude="{exclude}"'.format(
                tar_command=tar_command, exclude=self.exclude)

        tar_command = '{0} {1}'.format(tar_command, self.filepath)

        if self.encrypt_pass_file:
            openssl_cmd = "{openssl_path} enc -aes-256-cfb -pass file:{file}"\
                .format(openssl_path=self.openssl_path,
                        file=self.encrypt_pass_file)
            tar_command = '{0} | {1}'.format(tar_command, openssl_cmd)

        return tar_command


class TarCommandRestoreBuilder:
    WINDOWS_TEMPLATE = '{0} -x -z --incremental --unlink-first ' \
        '--ignore-zeros -f - '
    DRY_RUN_TEMPLATE = '{0} -z --incremental --list ' \
        '--ignore-zeros --warning=none'
    NORMAL_TEMPLATE = '{0} -z --incremental --extract --unlink-first ' \
        '--ignore-zeros --warning=none --overwrite --directory {1}'

    def __init__(self, tar_path, restore_path):
        self.dry_run = False
        self.is_windows = False
        self.openssl_path = None
        self.encrypt_pass_file = None
        self.tar_path = tar_path
        self.restore_path = restore_path
        self.archive = None

    def set_dry_run(self):
        self.dry_run = True

    def set_windows(self):
        self.is_windows = True

    def set_encryption(self, openssl_path, encrypt_pass_file):
        self.openssl_path = openssl_path
        self.encrypt_pass_file = encrypt_pass_file

    def set_archive(self, archive):
        self.archive = archive

    def build(self):
        if self.is_windows:
            tar_command = self.NORMAL_TEMPLATE.format(self.tar_path)
        elif self.dry_run:
            tar_command = self.DRY_RUN_TEMPLATE.format(self.tar_path)
        else:
            tar_command = self.NORMAL_TEMPLATE.format(self.tar_path,
                                                      self.restore_path)

        if self.archive:
            tar_command = tar_command + " --file " + self.archive
        # Check if encryption file is provided and set the openssl decrypt
        # command accordingly
        if self.encrypt_pass_file:
            openssl_cmd = "{openssl_path} enc -aes-256-cfb -pass file:{file}"\
                .format(openssl_path=self.openssl_path,
                        file=self.encrypt_pass_file)
            tar_command = '{0} | {1} '.format(openssl_cmd, tar_command)
        return tar_command


def tar_restore_args_valid(backup_opt_dict):
    required_list = [
        os.path.exists(backup_opt_dict.restore_abs_path)]
    try:
        valid_args = validate_all_args(required_list)   # might raise
        if not valid_args:
            raise Exception(('please provide ALL of the following '
                             'argument: --restore-abs-path'))
    except Exception as err:
        valid_args = False
        logging.critical('[*] Critical Error: {0}'.format(err))
    return valid_args


def tar_restore(restore_abs_path, tar_command, read_pipe):
    """
    Restore the provided file into backup_opt_dict.restore_abs_path
    Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided
    """

    if is_windows():
        # on windows, chdir to restore path.
        os.chdir(restore_abs_path)

    tar_cmd_proc = subprocess.Popen(
        tar_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    # Start loop reading the pipe and pass the data to the tar std input.
    # If EOFError exception is raised, the loop end the std err will be
    # checked for errors.
    try:
        while True:
            tar_cmd_proc.stdin.write(read_pipe.recv_bytes())
    except EOFError:
        logging.info(
            '[*] Pipe closed as EOF reached. Data transmitted succesfully')

    tar_err = tar_cmd_proc.communicate()[1]

    if 'error' in tar_err.lower():
        logging.exception('[*] Restore error: {0}'.format(tar_err))
        sys.exit(1)


def tar_backup(path_to_backup, max_segment_size, tar_command, backup_queue):
    """
    Execute an incremental backup using tar options, specified as
    function arguments
    """
    # Set counters, index, limits and bufsize for subprocess
    file_read_limit = 0
    file_chunk_index = 00000000
    tar_chunk = b''
    logging.info(
        '[*] Archiving and compressing files from {0}'.format(path_to_backup))

    tar_process = subprocess.Popen(
        tar_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True)

    # Iterate over tar process stdout
    for file_block in tar_process.stdout:
        tar_chunk += file_block
        file_read_limit += len(file_block)
        if file_read_limit >= max_segment_size:
            backup_queue.put(
                ({("%08d" % file_chunk_index): tar_chunk}))
            file_chunk_index += 1
            tar_chunk = b''
            file_read_limit = 0

    # Upload segments smaller then opt_dict.max_segment_size
    if len(tar_chunk) < max_segment_size:
        backup_queue.put(
            ({("%08d" % file_chunk_index): tar_chunk}))
