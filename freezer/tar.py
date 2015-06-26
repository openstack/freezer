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

    def __init__(self, path):
        self.dereference = ''
        self.path = path
        self.level = 0
        self.exclude = None
        self.dereference_mode = {
            'soft': '--dereference',
            'hard': '--hard-dereference',
            'all': '--hard-dereference --dereference',
            'none': ''
        }
        self.listed_incremental = None
        self.work_dir = None
        self.exclude = ''
        self.openssl_path = None
        self.encrypt_pass_file = None

    def set_level(self, level):
        self.level = level

    def set_work_dir(self, work_dir):
        self.work_dir = work_dir

    def set_listed_incremental(self, path):
        self.listed_incremental = path

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
        if mode not in self.dereference_mode:
            raise Exception("unknown dereference mode: %s" % mode)
        self.dereference = mode

    def set_encryption(self, openssl_path, encrypt_pass_file):
        self.openssl_path = openssl_path
        self.encrypt_pass_file = encrypt_pass_file

    def build(self):
        tar_command = ' {path} --create -z --warning=none --no-check-device \
            --one-file-system --preserve-permissions --same-owner --seek \
            --ignore-failed-read {dereference}'.format(
            path=self.path,
            dereference=self.dereference_mode[self.dereference])
        if self.listed_incremental:
            tar_command = '{tar_command} --level={level} \
            --listed-incremental={work_dir}/{listed_incremental}'.format(
                tar_command=tar_command,
                level=self.level,
                work_dir=self.work_dir,
                listed_incremental=self.listed_incremental)

        if self.exclude:
            tar_command = ' {tar_command} --exclude="{exclude}" '.format(
                tar_command=tar_command,
                exclude=self.exclude)

        if self.encrypt_pass_file:
            openssl_cmd = "{openssl_path} enc -aes-256-cfb -pass file:{file}"\
                .format(openssl_path=self.openssl_path,
                        file=self.encrypt_pass_file)
            tar_command = '{0} | {1} '.format(tar_command, openssl_cmd)

        return ' {0} . '.format(tar_command)


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


def tar_restore(backup_opt_dict, read_pipe):
    """
    Restore the provided file into backup_opt_dict.restore_abs_path
    Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided
    """

    if not tar_restore_args_valid(backup_opt_dict):
        sys.exit(1)

    if backup_opt_dict.dry_run:
        tar_cmd = ' {0} -z --incremental --list  \
            --ignore-zeros --warning=none'.format(
            backup_opt_dict.tar_path)
    else:
        tar_cmd = ' {0} -z --incremental --extract  \
            --unlink-first --ignore-zeros --warning=none --overwrite \
            --directory {1} '.format(
            backup_opt_dict.tar_path, backup_opt_dict.restore_abs_path)

    if is_windows():
        # on windows, chdir to restore path.
        os.chdir(backup_opt_dict.restore_abs_path)
        tar_cmd = '{0} -x -z --incremental --unlink-first ' \
                  '--ignore-zeros -f - '.format(backup_opt_dict.tar_path)

    # Check if encryption file is provided and set the openssl decrypt
    # command accordingly
    if backup_opt_dict.encrypt_pass_file:
        openssl_cmd = " {0} enc -d -aes-256-cfb -pass file:{1}".format(
            backup_opt_dict.openssl_path,
            backup_opt_dict.encrypt_pass_file)
        tar_cmd = '{0} | {1} '.format(openssl_cmd, tar_cmd)

    tar_cmd_proc = subprocess.Popen(
        tar_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def tar_backup(opt_dict, tar_command, backup_queue):
    """
    Execute an incremental backup using tar options, specified as
    function arguments
    """
    # Set counters, index, limits and bufsize for subprocess
    file_read_limit = 0
    file_chunk_index = 00000000
    tar_chunk = b''
    logging.info(
        '[*] Archiving and compressing files from {0}'.format(
            opt_dict.path_to_backup))

    tar_process = subprocess.Popen(
        tar_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True)

    # Iterate over tar process stdout
    for file_block in tar_process.stdout:
        tar_chunk += file_block
        file_read_limit += len(file_block)
        if file_read_limit >= opt_dict.max_segment_size:
            backup_queue.put(
                ({("%08d" % file_chunk_index): tar_chunk}))
            file_chunk_index += 1
            tar_chunk = b''
            file_read_limit = 0

    # Upload segments smaller then opt_dict.max_segment_size
    if len(tar_chunk) < opt_dict.max_segment_size:
        backup_queue.put(
            ({("%08d" % file_chunk_index): tar_chunk}))
