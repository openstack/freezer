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

from freezer.utils import (
    validate_all_args, add_host_name_ts_level, create_dir)
from freezer.swift import object_to_file

import os
import logging
import subprocess
import time


def tar_restore(backup_opt_dict, read_pipe):
    """
    Restore the provided file into backup_opt_dict.restore_abs_path
    Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided
    """

    # Validate mandatory arguments
    required_list = [
        os.path.exists(backup_opt_dict.restore_abs_path)]

    if not validate_all_args(required_list):
        logging.critical("[*] Error: please provide ALL of the following \
            arguments: {0}".format(' '.join(required_list)))
        raise ValueError

    # Set the default values for tar restore
    tar_cmd = ' {0} -z --incremental --extract  \
        --unlink-first --ignore-zeros --warning=none --overwrite \
        --directory {1} '.format(
        backup_opt_dict.tar_path, backup_opt_dict.restore_abs_path)

    # Check if encryption file is provided and set the openssl decrypt
    # command accordingly
    if backup_opt_dict.encrypt_pass_file:
        openssl_cmd = " {0} enc -d -aes-256-cfb -pass file:{1}".format(
            backup_opt_dict.openssl_path,
            backup_opt_dict.encrypt_pass_file)
        tar_cmd = ' {0} | {1} '.format(openssl_cmd, tar_cmd)

    tar_cmd_proc = subprocess.Popen(
        tar_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=backup_opt_dict.bash_path)

    # Start loop reading the pipe and pass the data to the tar std input.
    # If EOFError exception is raised, the loop end the std err will be
    # checked for errors.
    try:
        while True:
            tar_cmd_proc.stdin.write(read_pipe.recv_bytes())
    except EOFError:
        logging.info(
            '[*] Pipe closed as EOF reached. Data transmitted succesfully.')

    tar_err = tar_cmd_proc.communicate()[1]

    if 'error' in tar_err.lower():
        logging.exception('[*] Restore error: {0}'.format(tar_err))
        raise Exception(tar_err)


def tar_incremental(
        tar_cmd, backup_opt_dict, curr_tar_meta, remote_manifest_meta=None):
    """
    Check if the backup already exist in swift. If the backup already
    exists, the related meta data and the tar incremental meta file will be
    downloaded. According to the meta data content, new options will be
    provided for the next meta data upload to swift and the existing tar meta
    file will be used in the current incremental backup. Also the level
    options will be checked and updated respectively
    """

    if not tar_cmd or not backup_opt_dict:
        logging.error('[*] Error: tar_incremental, please provide tar_cmd \
        and  backup options')
        raise ValueError

    if not remote_manifest_meta:
        remote_manifest_meta = dict()
    # If returned object from check_backup is not a dict, the backup
    # is considered at first run, so a backup level 0 will be executed
    curr_backup_level = remote_manifest_meta.get(
        'x-object-meta-backup-current-level', '0')
    tar_meta = remote_manifest_meta.get(
        'x-object-meta-tar-meta-obj-name')
    tar_cmd_level = '--level={0} '.format(curr_backup_level)
    # Write the tar meta data file in ~/.freezer. It will be
    # removed later on. If ~/.freezer does not exists it will be created'.
    create_dir(backup_opt_dict.workdir)

    curr_tar_meta = '{0}/{1}'.format(
        backup_opt_dict.workdir, curr_tar_meta)
    tar_cmd_incr = ' --listed-incremental={0} '.format(curr_tar_meta)
    if tar_meta:
        # If tar meta data file is available, download it and use it
        # as for tar incremental backup. Afte this, the
        # remote_manifest_meta['x-object-meta-tar-meta-obj-name'] will be
        # update with the current tar meta data name and uploaded again
        tar_cmd_incr = ' --listed-incremental={0}/{1} '.format(
            backup_opt_dict.workdir, tar_meta)
        tar_meta_abs = "{0}/{1}".format(backup_opt_dict.workdir, tar_meta)
        try:
            object_to_file(
                backup_opt_dict, tar_meta_abs)
        except Exception:
            logging.warning(
                '[*] Tar metadata {0} not found. Executing level 0 backup\
                    '.format(tar_meta))

    tar_cmd = ' {0} {1} {2} '.format(tar_cmd, tar_cmd_level, tar_cmd_incr)
    return tar_cmd, backup_opt_dict, remote_manifest_meta


def gen_tar_command(
        opt_dict, meta_data_backup_file=False, time_stamp=int(time.time()),
        remote_manifest_meta=False):
    """
    Generate tar command options.
    """

    required_list = [
        opt_dict.backup_name,
        opt_dict.src_file,
        os.path.exists(opt_dict.src_file)]

    if not validate_all_args(required_list):
        logging.critical(
            'Error: Please ALL the following options: {0}'.format(
                ','.join(required_list)))
        raise Exception

    # Change che current working directory to op_dict.src_file
    os.chdir(os.path.normpath(opt_dict.src_file.strip()))

    logging.info('[*] Changing current working directory to: {0} \
    '.format(opt_dict.src_file))
    logging.info('[*] Backup started for: {0} \
    '.format(opt_dict.src_file))

    # Tar option for default behavior. Please refer to man tar to have
    # a better options explanation
    tar_command = ' {0} --create -z --warning=none \
        --no-check-device --one-file-system \
        --preserve-permissions --same-owner --seek \
        --ignore-failed-read '.format(opt_dict.tar_path)

    # Dereference hard and soft links according option choices.
    # 'soft' dereference soft links, 'hard' dereference hardlinks,
    # 'all' dereference both. Defaul 'none'.
    if opt_dict.dereference_symlink == 'soft':
        tar_command = ' {0} --dereference '.format(
            tar_command)
    if opt_dict.dereference_symlink == 'hard':
        tar_command = ' {0} --hard-dereference '.format(
            tar_command)
    if opt_dict.dereference_symlink == 'all':
        tar_command = ' {0} --hard-dereference --dereference '.format(
            tar_command)

    file_name = add_host_name_ts_level(opt_dict, time_stamp)
    meta_data_backup_file = u'tar_metadata_{0}'.format(file_name)
    # Incremental backup section
    if not opt_dict.no_incremental:
        (tar_command, opt_dict, remote_manifest_meta) = tar_incremental(
            tar_command, opt_dict, meta_data_backup_file,
            remote_manifest_meta)

    # End incremental backup section
    if opt_dict.exclude:
        tar_command = ' {0} --exclude="{1}" '.format(
            tar_command,
            opt_dict.exclude)

    tar_command = ' {0} . '.format(tar_command)
    # Encrypt data if passfile is provided
    if opt_dict.encrypt_pass_file:
        openssl_cmd = "{0} enc -aes-256-cfb -pass file:{1}".format(
            opt_dict.openssl_path, opt_dict.encrypt_pass_file)
        tar_command = '{0} | {1} '.format(tar_command, openssl_cmd)

    return opt_dict, tar_command, remote_manifest_meta


def tar_backup(opt_dict, tar_command, backup_queue):
    """
    Execute an incremental backup using tar options, specified as
    function arguments
    """

    # Set counters, index, limits and bufsize for subprocess
    buf_size = 1048576
    file_read_limit = 0
    file_chunk_index = 00000000
    tar_chunk = b''
    logging.info(
        '[*] Archiving and compressing files from {0}'.format(
            opt_dict.src_file))

    tar_process = subprocess.Popen(
        tar_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=buf_size, shell=True,
        executable=opt_dict.bash_path, env=os.environ.copy())

    # Iterate over tar process stdout
    for file_block in tar_process.stdout:
        tar_chunk += file_block
        file_read_limit += len(file_block)
        if file_read_limit >= opt_dict.max_seg_size:
            backup_queue.put(
                ({("%08d" % file_chunk_index): tar_chunk}))
            file_chunk_index += 1
            tar_chunk = b''
            file_read_limit = 0

    # Upload segments smaller then opt_dict.max_seg_size
    if len(tar_chunk) < opt_dict.max_seg_size:
        backup_queue.put(
            ({("%08d" % file_chunk_index): tar_chunk}))
