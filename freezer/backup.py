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

Freezer Backup modes related functions
"""
import logging
import os
from os.path import expanduser
import time

from freezer import utils
from freezer.lvm import lvm_snap, lvm_snap_remove, get_lvm_info
from freezer.tar import TarCommandBuilder
from freezer.vss import vss_create_shadow_copy
from freezer.vss import vss_delete_shadow_copy
from freezer.winutils import start_sql_server
from freezer.winutils import stop_sql_server
from freezer.winutils import use_shadow
from freezer.winutils import is_windows

home = expanduser("~")


def backup_mode_sql_server(backup_opt_dict):
    """
    Execute a SQL Server DB backup. Currently only backups with shadow
    copy are supported. This mean, as soon as the shadow copy is created
    the db writes will be blocked and a checkpoint will be created, as soon
    as the backup finish the db will be unlocked and the backup will be
    uploaded. A sql_server.conf_file is required for this operation.
    """
    with open(backup_opt_dict.sql_server_conf, 'r') as sql_conf_file_fd:
        for line in sql_conf_file_fd:
            if 'instance' in line and not line.strip().startswith("#"):
                db_instance = line.split('=')[1].strip()
                backup_opt_dict.sql_server_instance = db_instance
                continue
            else:
                raise Exception('Please indicate a valid SQL Server instance')

    try:
        stop_sql_server(backup_opt_dict)
        backup(backup_opt_dict, backup_opt_dict.storage)
    finally:
        if not backup_opt_dict.vssadmin:
            # if vssadmin is false, wait until the backup is complete
            # to start sql server again
            start_sql_server(backup_opt_dict)


def backup_mode_mysql(backup_opt_dict):
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
            if 'host' in line and not line.strip().startswith("#"):
                db_host = line.split('=')[1].strip()
                continue
            elif 'user' in line and not line.strip().startswith("#"):
                db_user = line.split('=')[1].strip()
                continue
            elif 'password' in line and not line.strip().startswith("#"):
                db_pass = line.split('=')[1].strip()
                continue
            elif 'port' in line and not line.strip().startswith("#"):
                try:
                    db_port = int(db_port)
                except ValueError:
                    raise ValueError('[*] MySQL port should be integer')
                continue

    # Initialize the DB object and connect to the db according to
    # the db mysql backup file config
    try:
        backup_opt_dict.mysql_db_inst = MySQLdb.connect(
            host=db_host, port=db_port, user=db_user, passwd=db_pass)
    except Exception as error:
        raise Exception('[*] MySQL: {0}'.format(error))

    # Execute backup
    backup(backup_opt_dict, backup_opt_dict.storage)


def backup_mode_mongo(backup_opt_dict):
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
        backup(backup_opt_dict, backup_opt_dict.storage)
    else:
        logging.warning('[*] localhost {0} is not Master/Primary,\
        exiting...'.format(local_hostname))
        return True


class BackupOs:

    def __init__(self, client_manager, container, storage):
        """

        :param client_manager:
        :param container:
        :param storage:
        :type storage: freezer.swift.SwiftStorage
        :return:
        """
        self.client_manager = client_manager
        self.container = container
        self.storage = storage

    def backup_nova(self, instance_id):
        """
        Implement nova backup
        :param instance_id: Id of the instance for backup
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
        package = "{0}/{1}".format(instance_id, utils.DateTime.now().timestamp)
        logging.info("[*] Uploading image to swift")
        headers = {"x-object-meta-name": instance._info['name'],
                   "x-object-meta-tenant_id": instance._info['tenant_id']}
        self.storage.add_stream(stream, package, headers)
        logging.info("[*] Deleting temporary image")
        glance.images.delete(image)

    def backup_cinder_by_glance(self, volume_id):
        """
        Implements cinder backup:
            1) Gets a stream of the image from glance
            2) Stores resulted image to the swift as multipart object

        :param volume_id: id of volume for backup
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
        package = "{0}/{1}".format(volume_id, utils.DateTime.now().timestamp)
        logging.info("[*] Uploading image to swift")
        headers = {}
        self.storage.add_stream(stream, package, headers=headers)
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


def snapshot_create(backup_opt_dict):
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
            lvm_list = get_lvm_info(
                backup_opt_dict.lvm_auto_snap)
            backup_opt_dict.lvm_volgroup = lvm_list[0]
            backup_opt_dict.lvm_srcvol = lvm_list[2]

        # Generate the lvm_snap if lvm arguments are available
        lvm_snap(backup_opt_dict)

    if is_windows() and backup_opt_dict.vssadmin:
        backup_opt_dict.path_to_backup = use_shadow(
            backup_opt_dict.path_to_backup,
            backup_opt_dict.windows_volume)
    return backup_opt_dict


def snapshot_remove(backup_opt_dict, shadow, windows_volume):
    if is_windows():
        # Delete the shadow copy after the backup
        vss_delete_shadow_copy(shadow, windows_volume)
    else:
        # Unmount and remove lvm snapshot volume
        lvm_snap_remove(backup_opt_dict)


def backup(backup_opt_dict, storage):
    """

    :param backup_opt_dict:
    :param storage:
    :type storage: freezer.storage.Storage
    :return:
    """
    backup_media = backup_opt_dict.backup_media

    if backup_media == 'fs':

        try:
            backup_opt_dict = snapshot_create(backup_opt_dict)
            filepath = '.'
            chdir_path = os.path.expanduser(
                os.path.normpath(backup_opt_dict.path_to_backup.strip()))
            if not os.path.isdir(chdir_path):
                filepath = os.path.basename(chdir_path)
                chdir_path = os.path.dirname(chdir_path)
            os.chdir(chdir_path)
            builder = TarCommandBuilder(backup_opt_dict.tar_path,
                                        filepath,
                                        backup_opt_dict.compression)
            builder.set_dereference(backup_opt_dict.dereference_symlink)
            if backup_opt_dict.exclude:
                builder.set_exclude(backup_opt_dict.exclude)
            if backup_opt_dict.encrypt_pass_file:
                builder.set_encryption(
                    backup_opt_dict.openssl_path,
                    backup_opt_dict.encrypt_pass_file)
            hostname_backup_name = backup_opt_dict.hostname_backup_name
            if not storage.is_ready():
                storage.prepare()
            incremental_backup = storage.find_previous_backup(
                hostname_backup_name,
                backup_opt_dict.no_incremental,
                backup_opt_dict.max_level,
                backup_opt_dict.always_level,
                backup_opt_dict.restart_always_level)
            storage.backup(backup_opt_dict.path_to_backup,
                           hostname_backup_name, builder, incremental_backup)
        finally:
            snapshot_remove(backup_opt_dict, backup_opt_dict.shadow,
                            backup_opt_dict.windows_volume)
        return

    backup_os = BackupOs(backup_opt_dict.client_manager,
                         backup_opt_dict.container,
                         storage)

    if backup_media == 'nova':
        logging.info('[*] Executing nova backup')
        backup_os.backup_nova(backup_opt_dict.nova_inst_id)
    elif backup_media == 'cindernative':
        logging.info('[*] Executing cinder backup')
        backup_os.backup_cinder(backup_opt_dict.cindernative_vol_id)
    elif backup_media == 'cinder':
        logging.info('[*] Executing cinder snapshot')
        backup_os.backup_cinder_by_glance(backup_opt_dict.cindernative_vol_id)
    else:
        raise Exception('unknown parameter backup_media %s' % backup_media)
