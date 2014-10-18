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

Freezer Backup modes related functions
"""

from freezer.lvm import lvm_snap, lvm_snap_remove, get_lvm_info
from freezer.tar import tar_backup, gen_tar_command
from freezer.swift import add_object, manifest_upload, get_client
from freezer.utils import gen_manifest_meta, add_host_name_ts_level

from multiprocessing import Process, Queue
import logging
import os


def backup_mode_mysql(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute a MySQL DB backup. currently only backup with lvm snapshots
    are supported. This mean, just before the lvm snap vol is created,
    the db tables will be flushed and locked for read, then the lvm create
    command will be executed and after that, the table will be unlocked and
    the backup will be executed. It is important to have the available in
    backup_args.mysql_conf_file the file where the database host, name, user,
    and password are set.
    """

    try:
        import MySQLdb
    except ImportError as error:
        logging.critical('[*] Error: please install MySQLdb module')
        raise ImportError('[*] Error: please install MySQLdb module')

    if not backup_opt_dict.mysql_conf_file:
        logging.critical(
            '[*] MySQL Error: please provide a valid config file')
        raise ValueError
    # Open the file provided in backup_args.mysql_conf_file and extract the
    # db host, name, user and password.
    db_user = db_host = db_pass = False
    with open(backup_opt_dict.mysql_conf_file, 'r') as mysql_file_fd:
        for line in mysql_file_fd:
            if 'host' in line:
                db_host = line.split('=')[1].strip()
                continue
            elif 'user' in line:
                db_user = line.split('=')[1].strip()
                continue
            elif 'password' in line:
                db_pass = line.split('=')[1].strip()
                continue

    # Initialize the DB object and connect to the db according to
    # the db mysql backup file config
    try:
        backup_opt_dict.mysql_db_inst = MySQLdb.connect(
            host=db_host, user=db_user, passwd=db_pass)
    except Exception as error:
        logging.critical('[*] MySQL Error: {0}'.format(error))
        raise Exception('[*] MySQL Error: {0}'.format(error))

    # Execute LVM backup
    backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict)


def backup_mode_mongo(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute the necessary tasks for file system backup mode
    """

    try:
        from pymongo import MongoClient
    except ImportError:
        logging.critical('[*] Error: please install pymongo module')
        raise ImportError('[*] Error: please install pymongo module')

    logging.info('[*] MongoDB backup is being executed...')
    logging.info('[*] Checking is the localhost is Master/Primary...')
    mongodb_port = '27017'
    local_hostname = backup_opt_dict.hostname
    db_host_port = '{0}:{1}'.format(local_hostname, mongodb_port)
    mongo_client = MongoClient(db_host_port)
    master_dict = dict(mongo_client.admin.command("isMaster"))
    mongo_me = master_dict['me']
    mongo_primary = master_dict['primary']

    if mongo_me == mongo_primary:
        backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict)
    else:
        logging.warning('[*] localhost {0} is not Master/Primary,\
        exiting...'.format(local_hostname))
        return True


def backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute the necessary tasks for file system backup mode
    """

    logging.info('[*] File System backup is being executed...')

    # If lvm_auto_snap is true, the volume group and volume name will be
    # extracted automatically
    if backup_opt_dict.lvm_auto_snap:
        backup_opt_dict = get_lvm_info(backup_opt_dict)

    # Generate the lvm_snap if lvm arguments are available
    lvm_snap(backup_opt_dict)

    # Generate a string hostname, backup name, timestamp and backup level
    file_name = add_host_name_ts_level(backup_opt_dict, time_stamp)
    meta_data_backup_file = u'tar_metadata_{0}'.format(file_name)

    # Execute a tar gzip of the specified directory and return
    # small chunks (default 128MB), timestamp, backup, filename,
    # file chunk index and the tar meta-data file
    (backup_opt_dict, tar_command, manifest_meta_dict) = gen_tar_command(
        opt_dict=backup_opt_dict, time_stamp=time_stamp,
        remote_manifest_meta=manifest_meta_dict)
    # Initialize a Queue for a maximum of 2 items
    tar_backup_queue = Queue(maxsize=2)
    tar_backup_stream = Process(
        target=tar_backup, args=(
            backup_opt_dict, tar_command, tar_backup_queue,))
    tar_backup_stream.daemon = True
    tar_backup_stream.start()

    add_object_stream = Process(
        target=add_object, args=(
            backup_opt_dict, tar_backup_queue, file_name, time_stamp))
    add_object_stream.daemon = True
    add_object_stream.start()

    tar_backup_stream.join()
    tar_backup_queue.put(({False: False}))
    tar_backup_queue.close()
    add_object_stream.join()

    (backup_opt_dict, manifest_meta_dict, tar_meta_to_upload,
        tar_meta_prev) = gen_manifest_meta(
            backup_opt_dict, manifest_meta_dict, meta_data_backup_file)

    manifest_file = u''
    meta_data_abs_path = '{0}/{1}'.format(
        backup_opt_dict.workdir, tar_meta_prev)

    # Upload swift manifest for segments
    if backup_opt_dict.upload:
        # Request a new auth client in case the current token
        # is expired before uploading tar meta data or the swift manifest
        backup_opt_dict = get_client(backup_opt_dict)

        if not backup_opt_dict.no_incremental:
            # Upload tar incremental meta data file and remove it
            logging.info('[*] Uploading tar meta data file: {0}'.format(
                tar_meta_to_upload))
            with open(meta_data_abs_path, 'r') as meta_fd:
                backup_opt_dict.sw_connector.put_object(
                    backup_opt_dict.container, tar_meta_to_upload, meta_fd)
            # Removing tar meta data file, so we have only one authoritative
            # version on swift
            logging.info('[*] Removing tar meta data file: {0}'.format(
                meta_data_abs_path))
            os.remove(meta_data_abs_path)
        # Upload manifest to swift
        manifest_upload(
            manifest_file, backup_opt_dict, file_name, manifest_meta_dict)

    # Unmount and remove lvm snapshot volume
    lvm_snap_remove(backup_opt_dict)
