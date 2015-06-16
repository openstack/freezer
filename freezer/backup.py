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
import multiprocessing
import logging
import os
from os.path import expanduser
import time

from freezer.lvm import lvm_snap, lvm_snap_remove, get_lvm_info
from freezer.tar import tar_backup, TarCommandBuilder
from freezer.utils import gen_manifest_meta, create_dir
from freezer.vss import vss_create_shadow_copy
from freezer.vss import vss_delete_shadow_copy
from freezer.winutils import start_sql_server
from freezer.winutils import stop_sql_server
from freezer.winutils import use_shadow
from freezer.winutils import is_windows
from freezer import swift

home = expanduser("~")


def backup_mode_sql_server(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute a SQL Server DB backup. Currently only backups with shadow
    copy are supported. This mean, as soon as the shadow copy is created
    the db writes will be blocked and a checkpoint will be created, as soon
    as the backup finish the db will be unlocked and the backup will be
    uploaded. A sql_server.conf_file is required for this operation.
    """
    with open(backup_opt_dict.sql_server_conf, 'r') as sql_conf_file_fd:
        for line in sql_conf_file_fd:
            if 'instance' in line:
                db_instance = line.split('=')[1].strip()
                backup_opt_dict.sql_server_instance = db_instance
                continue
            else:
                raise Exception('Please indicate a valid SQL Server instance')

    try:
        stop_sql_server(backup_opt_dict)
        backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict)
    finally:
        if not backup_opt_dict.vssadmin:
            # if vssadmin is false, wait until the backup is complete
            # to start sql server again
            start_sql_server(backup_opt_dict)


def backup_mode_mysql(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute a MySQL DB backup. currently only backup with lvm snapshots
    are supported. This mean, just before the lvm snap vol is created,
    the db tables will be flushed and locked for read, then the lvm create
    command will be executed and after that, the table will be unlocked and
    the backup will be executed. It is important to have the available in
    backup_args.mysql_conf the file where the database host, name, user,
    password and port are set.
    """

    try:
        import pymysql as MySQLdb
    except ImportError:
        raise ImportError('Please install PyMySQL module')

    if not backup_opt_dict.mysql_conf:
        raise ValueError('MySQL: please provide a valid config file')
    # Open the file provided in backup_args.mysql_conf and extract the
    # db host, name, user, password and port.
    db_user = db_host = db_pass = False
    # Use the default mysql port if not provided
    db_port = 3306
    with open(backup_opt_dict.mysql_conf, 'r') as mysql_file_fd:
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
            elif 'port' in line:
                db_port = line.split('=')[1].strip()
                continue

    # Initialize the DB object and connect to the db according to
    # the db mysql backup file config
    try:
        backup_opt_dict.mysql_db_inst = MySQLdb.connect(
            host=db_host, port=db_port, user=db_user, passwd=db_pass)
    except Exception as error:
        raise Exception('[*] MySQL: {0}'.format(error))

    # Execute backup
    backup(backup_opt_dict, time_stamp, manifest_meta_dict)


def backup_mode_mongo(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute the necessary tasks for file system backup mode
    """

    try:
        import pymongo
    except ImportError:
        raise ImportError('please install pymongo module')

    logging.info('[*] MongoDB backup is being executed...')
    logging.info('[*] Checking is the localhost is Master/Primary...')
    mongodb_port = '27017'
    local_hostname = backup_opt_dict.hostname
    db_host_port = '{0}:{1}'.format(local_hostname, mongodb_port)
    mongo_client = pymongo.MongoClient(db_host_port)
    master_dict = dict(mongo_client.admin.command("isMaster"))
    mongo_me = master_dict['me']
    mongo_primary = master_dict['primary']

    if mongo_me == mongo_primary:
        backup(backup_opt_dict, time_stamp, manifest_meta_dict)
    else:
        logging.warning('[*] localhost {0} is not Master/Primary,\
        exiting...'.format(local_hostname))
        return True


class BackupOs:

    def __init__(self, client_manager, container):
        self.client_manager = client_manager
        self.container = container

    def backup_nova(self, instance_id, time_stamp):
        """
        Implement nova backup
        :param instance_id: Id of the instance for backup
        :param time_stamp: timestamp of backup
        :return:
        """
        instance_id = instance_id
        client_manager = self.client_manager
        nova = client_manager.get_nova()
        instance = nova.servers.get(instance_id)
        glance = client_manager.get_glance()

        if instance.__dict__['OS-EXT-STS:task_state']:
            time.sleep(5)
            instance = nova.servers.get(instance)

        image = instance.create_image("snapshot_of_%s" % instance_id)
        image = glance.images.get(image)
        while image.status != 'active':
            time.sleep(5)
            image = glance.images.get(image)

        stream = client_manager.download_image(image)
        package = "{0}/{1}".format(instance_id, time_stamp)
        logging.info("[*] Uploading image to swift")
        headers = {"x-object-meta-name": instance._info['name'],
                   "x-object-meta-tenant_id": instance._info['tenant_id']}
        swift.add_stream(client_manager,
                         self.container, stream, package, headers)
        logging.info("[*] Deleting temporary image")
        glance.images.delete(image)

    def backup_cinder_by_glance(self, volume_id, time_stamp):
        """
        Implements cinder backup:
            1) Gets a stream of the image from glance
            2) Stores resulted image to the swift as multipart object

        :param volume_id: id of volume for backup
        :param time_stamp: timestamp of snapshot
        """
        client_manager = self.client_manager
        cinder = client_manager.get_cinder()

        volume = cinder.volumes.get(volume_id)
        logging.info("[*] Creation temporary snapshot")
        snapshot = client_manager.provide_snapshot(
            volume, "backup_snapshot_for_volume_%s" % volume_id)
        logging.info("[*] Creation temporary volume")
        copied_volume = client_manager.do_copy_volume(snapshot)
        logging.info("[*] Creation temporary glance image")
        image = client_manager.make_glance_image("name", copied_volume)
        stream = client_manager.download_image(image)
        package = "{0}/{1}".format(volume_id, time_stamp)
        logging.info("[*] Uploading image to swift")
        headers = {}
        swift.add_stream(self.client_manager,
                         self.container, stream, package, headers=headers)
        logging.info("[*] Deleting temporary snapshot")
        client_manager.clean_snapshot(snapshot)
        logging.info("[*] Deleting temporary volume")
        cinder.volumes.delete(copied_volume)
        logging.info("[*] Deleting temporary image")
        client_manager.get_glance().images.delete(image)

    def backup_cinder(self, volume_id, name=None, description=None):
        client_manager = self.client_manager
        cinder = client_manager.get_cinder()
        cinder.backups.create(volume_id, self.container, name, description)


def backup(backup_opt_dict, time_stamp, manifest_meta_dict):
    backup_media = backup_opt_dict.backup_media
    backup_os = BackupOs(backup_opt_dict.client_manager,
                         backup_opt_dict.container)
    if backup_media == 'fs':
        backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict)
    elif backup_media == 'nova':
        logging.info('[*] Executing nova backup')
        backup_os.backup_nova(backup_opt_dict.nova_inst_id, time_stamp)
    elif backup_media == 'cindernative':
        logging.info('[*] Executing cinder backup')
        backup_os.backup_cinder(backup_opt_dict.cindernative_vol_id)
    elif backup_media == 'cinder':
        logging.info('[*] Executing cinder snapshot')
        backup_os.backup_cinder_by_glance(backup_opt_dict.cindernative_vol_id,
                                          time_stamp)
    else:
        raise Exception('unknown parameter backup_media %s' % backup_media)


def backup_mode_fs(backup_opt_dict, time_stamp, manifest_meta_dict):
    """
    Execute the necessary tasks for file system backup mode
    """

    logging.info('[*] File System backup is being executed...')
    try:

        if is_windows():
            if backup_opt_dict.vssadmin:
                # Create a shadow copy.
                backup_opt_dict.shadow_path, backup_opt_dict.shadow = \
                    vss_create_shadow_copy(backup_opt_dict.windows_volume)

                # execute this after the snapshot creation
                if backup_opt_dict.mode == 'sqlserver':
                    start_sql_server(backup_opt_dict)

        else:
            # If lvm_auto_snap is true, the volume group and volume name will
            # be extracted automatically
            if backup_opt_dict.lvm_auto_snap:
                backup_opt_dict = get_lvm_info(backup_opt_dict)

            # Generate the lvm_snap if lvm arguments are available
            lvm_snap(backup_opt_dict)

        file_name_f = u'{0}_{1}_{2}_{3}'.format(
            backup_opt_dict.hostname,
            backup_opt_dict.backup_name,
            time_stamp,
            backup_opt_dict.curr_backup_level)
        meta_data_backup_file = u'tar_metadata_{0}'.format(file_name_f)

        # Initialize a Queue for a maximum of 2 items
        tar_backup_queue = multiprocessing.Queue(maxsize=2)

        if is_windows():
            backup_opt_dict.absolute_path = backup_opt_dict.path_to_backup
            if backup_opt_dict.vssadmin:
                backup_opt_dict.path_to_backup = use_shadow(
                    backup_opt_dict.path_to_backup,
                    backup_opt_dict.windows_volume)

        path_to_backup = backup_opt_dict.path_to_backup
        # Change che current working directory to op_dict.path_to_backup
        os.chdir(os.path.normpath(path_to_backup.strip()))

        logging.info('[*] Changing current working directory to: {0} \
        '.format(path_to_backup))
        logging.info('[*] Backup started for: {0}'.format(path_to_backup))

        builder = TarCommandBuilder(backup_opt_dict.tar_path)
        builder.set_dereference(backup_opt_dict.dereference_symlink)
        curr_backup_level = manifest_meta_dict.get(
            'x-object-meta-backup-current-level', '0')
        tar_meta = manifest_meta_dict.get('x-object-meta-tar-meta-obj-name')

        if not backup_opt_dict.no_incremental:
            builder.set_level(curr_backup_level)
            builder.set_work_dir(backup_opt_dict.work_dir)
            if tar_meta:
                builder.set_listed_incremental(tar_meta)
            else:
                builder.set_listed_incremental(meta_data_backup_file)
        if backup_opt_dict.exclude:
            builder.set_exclude(backup_opt_dict.exclude)

        # Incremental backup section
        if not backup_opt_dict.no_incremental:

            if not os.path.exists(backup_opt_dict.path_to_backup):
                raise Exception('Error: path-to-backup does not exist')
            # Write the tar meta data file in ~/.freezer. It will be
            # removed later on. If ~/.freezer does not exists it will
            # be created'.
            create_dir(backup_opt_dict.work_dir)

            if tar_meta:
                sw_connector = backup_opt_dict.client_manager.get_swift()
                tar_meta_abs = "{0}/{1}".format(backup_opt_dict.work_dir,
                                                tar_meta)

                file_name = tar_meta_abs.split('/')[-1]
                logging.info('[*] Downloading object {0} on {1}'.format(
                             file_name, tar_meta_abs))

                if os.path.exists(tar_meta_abs):
                    os.remove(tar_meta_abs)

                with open(tar_meta_abs, 'ab') as obj_fd:
                    for obj_chunk in sw_connector.get_object(
                            backup_opt_dict.container, file_name,
                            resp_chunk_size=16000000)[1]:
                        obj_fd.write(obj_chunk)

        # Encrypt data if passfile is provided
        if backup_opt_dict.encrypt_pass_file:
            builder.set_encryption(
                backup_opt_dict.openssl_path,
                backup_opt_dict.encrypt_pass_file)

        tar_backup_stream = multiprocessing.Process(
            target=tar_backup, args=(
                backup_opt_dict, builder.build(), tar_backup_queue,))

        tar_backup_stream.daemon = True
        tar_backup_stream.start()

        add_object = backup_opt_dict.storage.add_object

        add_object_stream = multiprocessing.Process(
            target=add_object, args=(
                backup_opt_dict.max_segment_size, tar_backup_queue,
                file_name_f, time_stamp))
        add_object_stream.daemon = True
        add_object_stream.start()

        tar_backup_stream.join()
        tar_backup_queue.put(({False: False}))
        tar_backup_queue.close()
        add_object_stream.join()

        if add_object_stream.exitcode:
            raise Exception('failed to upload object to swift server')

        (backup_opt_dict, manifest_meta_dict, tar_meta_to_upload,
            tar_meta_prev) = gen_manifest_meta(
                backup_opt_dict, manifest_meta_dict, meta_data_backup_file)

        meta_data_abs_path = os.path.join(backup_opt_dict.work_dir,
                                          tar_meta_prev)

        client_manager = backup_opt_dict.client_manager
        # Upload swift manifest for segments
        if backup_opt_dict.upload:
            # Request a new auth client in case the current token
            # is expired before uploading tar meta data or the swift manifest
            client_manager.create_swift()

            if not backup_opt_dict.no_incremental:
                # Upload tar incremental meta data file and remove it
                logging.info('[*] Uploading tar meta data file: {0}'.format(
                    tar_meta_to_upload))
                with open(meta_data_abs_path, 'r') as meta_fd:
                    client_manager.get_swift().put_object(
                        backup_opt_dict.container, tar_meta_to_upload, meta_fd)
                # Removing tar meta data file, so we have only one
                # authoritative version on swift
                logging.info('[*] Removing tar meta data file: {0}'.format(
                    meta_data_abs_path))
                os.remove(meta_data_abs_path)
            backup_opt_dict.storage.upload_manifest(file_name_f,
                                                    manifest_meta_dict)

    finally:
        if is_windows():
            # Delete the shadow copy after the backup
            vss_delete_shadow_copy(backup_opt_dict.shadow,
                                   backup_opt_dict.windows_volume)
        else:
            # Unmount and remove lvm snapshot volume
            lvm_snap_remove(backup_opt_dict)
