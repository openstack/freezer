"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
(C) Copyright 2016 Hewlett Packard Enterprise Development Company LP

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

import abc
import datetime
import os
import sys
import time

from oslo_config import cfg
from oslo_log import log
from oslo_utils import importutils
import six

from freezer.openstack import backup
from freezer.openstack import restore
from freezer.snapshot import snapshot
from freezer.utils import checksum
from freezer.utils import exec_cmd
from freezer.utils import utils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Job(object):
    """
    :type storage: freezer.storage.base.Storage
    :type engine: freezer.engine.engine.BackupEngine
    """

    def __init__(self, conf_dict, storage):
        self.conf = conf_dict
        self.storage = storage
        self.engine = conf_dict.engine
        self._general_validation()
        self._validate()

    @abc.abstractmethod
    def _validate(self):
        """
        Method that validates if all arguments available to execute the job
        or not
        :return: True or raise an error
        """
        pass

    def _general_validation(self):
        """
        Apply general validation rules.
        :return: True or raise an error
        """
        LOG.info("Validating args for the {0} job.".format(self.conf.action))
        if not self.conf.action:
            raise ValueError("Please provide a valid action with --action")

        if self.conf.action in ('backup', 'restore', 'admin') \
                and self.conf.backup_media == 'fs' \
                and not self.conf.backup_name:
            raise ValueError('A value for --backup-name is required')

    @abc.abstractmethod
    def execute(self):
        pass


class InfoJob(Job):

    def _validate(self):
        # no validation required for this job
        pass

    def execute(self):
        info = self.storage.info()
        if not info:
            return
        fields = ["Container", "Size", "Object Count"]
        data = []
        for container in info:
            values = [
                container.get('container_name'),
                container.get('size'),
                container.get('objects_count')
            ]
            data.append(values)
        return [fields, data]


class BackupJob(Job):

    def _validate(self):
        if self.conf.mode == 'fs':
            if not self.conf.path_to_backup:
                raise ValueError('path-to-backup argument must be provided')
            if self.conf.no_incremental and (self.conf.max_level or
                                             self.conf.always_level):
                raise Exception(
                    'no-incremental option is not compatible '
                    'with backup level options')
        if self.conf.mode == 'nova':
            if not self.conf.no_incremental:
                raise ValueError("Incremental nova backup is not supported")

            if not self.conf.nova_inst_id and not self.conf.project_id:
                raise ValueError("nova-inst-id or project-id"
                                 " argument must be provided")

        if self.conf.mode == 'cinder':
            if not self.conf.cinder_vol_id:
                raise ValueError("cinder-vol-id argument must be provided")

        if self.conf.mode == "cindernative":
            if not self.conf.cindernative_vol_id:
                raise ValueError("cindernative-vol-id"
                                 " argument must be provided")

    def execute(self):
        LOG.info('Backup job started. '
                 'backup_name: {0}, container: {1}, hostname: {2}, mode: {3},'
                 ' Storage: {4}, compression: {5}'
                 .format(self.conf.backup_name, self.conf.container,
                         self.conf.hostname, self.conf.mode, self.conf.storage,
                         self.conf.compression))
        try:
            if self.conf.mode is 'fs' and self.conf.sync:
                LOG.info('Executing sync to flush the file system buffer.')
                (out, err) = utils.create_subprocess('sync')
                if err:
                    LOG.error('Error while sync exec: {0}'.format(err))
        except Exception as error:
            LOG.error('Error while sync exec: {0}'.format(error))
        if not self.conf.mode:
            raise ValueError("Empty mode")
        mod_name = 'freezer.mode.{0}.{1}'.format(
            self.conf.mode, self.conf.mode.capitalize() + 'Mode')
        app_mode = importutils.import_object(mod_name, self.conf)
        backup_level = self.backup(app_mode)
        level = backup_level or 0

        metadata = {
            'curr_backup_level': level,
            'fs_real_path': self.conf.path_to_backup,
            'vol_snap_path': self.conf.path_to_backup,
            'client_os': sys.platform,
            'client_version': self.conf.__version__,
            'time_stamp': self.conf.time_stamp,
        }
        fields = ['action',
                  'always_level',
                  'backup_media',
                  'backup_name',
                  'container',
                  'container_segments',
                  'dry_run',
                  'hostname',
                  'path_to_backup',
                  'max_level',
                  'mode',
                  'backup_name',
                  'time_stamp',
                  'log_file',
                  'storage',
                  'mode',
                  'os_auth_version',
                  'proxy',
                  'compression',
                  'ssh_key',
                  'ssh_username',
                  'ssh_host',
                  'ssh_port',
                  'consistency_checksum'
                  ]
        for field_name in fields:
            metadata[field_name] = self.conf.__dict__.get(field_name, '') or ''
        return metadata

    def backup(self, app_mode):
        """

        :type app_mode: freezer.mode.mode.Mode
        :return:
        """
        backup_media = self.conf.backup_media

        time_stamp = utils.DateTime.now().timestamp
        self.conf.time_stamp = time_stamp

        if backup_media == 'fs':
            LOG.info('Path to backup: {0}'.format(self.conf.path_to_backup))
            app_mode.prepare()
            snapshot_taken = snapshot.snapshot_create(self.conf)
            if snapshot_taken:
                app_mode.release()
            try:
                filepath = '.'
                chdir_path = os.path.expanduser(
                    os.path.normpath(self.conf.path_to_backup.strip()))
                if not os.path.exists(chdir_path):
                    msg = 'Path to backup does not exist {0}'.format(
                        chdir_path)
                    LOG.critical(msg)
                    raise IOError(msg)
                if not os.path.isdir(chdir_path):
                    filepath = os.path.basename(chdir_path)
                    chdir_path = os.path.dirname(chdir_path)
                os.chdir(chdir_path)

                # Checksum for Backup Consistency
                if self.conf.consistency_check:
                    ignorelinks = (self.conf.dereference_symlink is None or
                                   self.conf.dereference_symlink == 'hard')
                    consistency_checksum = checksum.CheckSum(
                        filepath, ignorelinks=ignorelinks).compute()
                    LOG.info('Computed checksum for consistency {0}'.
                             format(consistency_checksum))
                    self.conf.consistency_checksum = consistency_checksum

                return self.engine.backup(
                    backup_resource=filepath,
                    hostname_backup_name=self.conf.hostname_backup_name,
                    no_incremental=self.conf.no_incremental,
                    max_level=self.conf.max_level,
                    always_level=self.conf.always_level,
                    restart_always_level=self.conf.restart_always_level)

            finally:
                # whether an error occurred or not, remove the snapshot anyway
                app_mode.release()
                if snapshot_taken:
                    snapshot.snapshot_remove(
                        self.conf, self.conf.shadow,
                        self.conf.windows_volume)

        backup_os = backup.BackupOs(self.conf.client_manager,
                                    self.conf.container,
                                    self.storage)

        if backup_media == 'nova':
            if self.conf.project_id:
                return self.engine.backup_nova_tenant(
                    project_id=self.conf.project_id,
                    hostname_backup_name=self.conf.hostname_backup_name,
                    no_incremental=self.conf.no_incremental,
                    max_level=self.conf.max_level,
                    always_level=self.conf.always_level,
                    restart_always_level=self.conf.restart_always_level)
            else:
                LOG.info('Executing nova backup. Instance ID: {0}'.format(
                    self.conf.nova_inst_id))
                hostname_backup_name = os.path.join(
                    self.conf.hostname_backup_name,
                    self.conf.nova_inst_id)
                return self.engine.backup(
                    backup_resource=self.conf.nova_inst_id,
                    hostname_backup_name=hostname_backup_name,
                    no_incremental=self.conf.no_incremental,
                    max_level=self.conf.max_level,
                    always_level=self.conf.always_level,
                    restart_always_level=self.conf.restart_always_level)

        elif backup_media == 'cindernative':
            LOG.info('Executing cinder native backup. Volume ID: {0}, '
                     'incremental: {1}'.format(self.conf.cindernative_vol_id,
                                               self.conf.incremental))
            backup_os.backup_cinder(self.conf.cindernative_vol_id,
                                    name=self.conf.backup_name,
                                    incremental=self.conf.incremental)
        elif backup_media == 'cinder':
            LOG.info('Executing cinder snapshot. Volume ID: {0}'.format(
                self.conf.cinder_vol_id))
            backup_os.backup_cinder_by_glance(self.conf.cinder_vol_id)
        elif backup_media == 'cinderbrick':
            LOG.info('Executing cinder volume backup using os-brick. '
                     'Volume ID: {0}'.format(self.conf.cinderbrick_vol_id))
            return self.engine.backup(
                backup_resource=self.conf.cinderbrick_vol_id,
                hostname_backup_name=self.conf.hostname_backup_name,
                no_incremental=self.conf.no_incremental,
                max_level=self.conf.max_level,
                always_level=self.conf.always_level,
                restart_always_level=self.conf.restart_always_level)
        else:
            raise Exception('unknown parameter backup_media %s' % backup_media)
        return None


class RestoreJob(Job):

    def _validate(self):
        if not any([self.conf.restore_abs_path,
                    self.conf.nova_inst_id,
                    self.conf.cinder_vol_id,
                    self.conf.cindernative_vol_id,
                    self.conf.cinderbrick_vol_id,
                    self.conf.project_id]):
            raise ValueError("--restore-abs-path is required")
        if not self.conf.container:
            raise ValueError("--container is required")
        if self.conf.no_incremental and (self.conf.max_level or
                                         self.conf.always_level):
            raise Exception(
                'no-incremental option is not compatible '
                'with backup level options')

    def execute(self):
        conf = self.conf
        LOG.info('Executing Restore...')
        restore_timestamp = None

        restore_abs_path = conf.restore_abs_path
        if conf.restore_from_date:
            restore_timestamp = utils.date_to_timestamp(conf.restore_from_date)
        if conf.backup_media == 'fs':
            self.engine.restore(
                hostname_backup_name=self.conf.hostname_backup_name,
                restore_resource=restore_abs_path,
                overwrite=conf.overwrite,
                recent_to_date=restore_timestamp,
                backup_media=conf.mode)

            try:
                if conf.consistency_checksum:
                    backup_checksum = conf.consistency_checksum
                    restore_checksum = checksum.CheckSum(restore_abs_path,
                                                         ignorelinks=True)
                    if restore_checksum.compare(backup_checksum):
                        LOG.info('Consistency check success.')
                    else:
                        raise ConsistencyCheckException(
                            "Backup Consistency Check failed: backup checksum "
                            "({0}) and restore checksum ({1}) did not match.".
                            format(backup_checksum, restore_checksum.checksum))
            except OSError as e:
                raise ConsistencyCheckException(
                    "Backup Consistency Check failed: could not checksum file"
                    " {0} ({1})".format(e.filename, e.strerror))
            return {}
        res = restore.RestoreOs(conf.client_manager, conf.container,
                                self.storage)
        if conf.backup_media == 'nova':
            if self.conf.project_id:
                return self.engine.restore_nova_tenant(
                    project_id=self.conf.project_id,
                    hostname_backup_name=self.conf.hostname_backup_name,
                    overwrite=conf.overwrite,
                    recent_to_date=restore_timestamp)
            else:
                LOG.info("Restoring nova backup. Instance ID: {0}, "
                         "timestamp: {1} network-id {2}".format(
                             conf.nova_inst_id,
                             restore_timestamp,
                             conf.nova_restore_network))
                hostname_backup_name = os.path.join(
                    self.conf.hostname_backup_name,
                    self.conf.nova_inst_id)
                self.engine.restore(
                    hostname_backup_name=hostname_backup_name,
                    restore_resource=conf.nova_inst_id,
                    overwrite=conf.overwrite,
                    recent_to_date=restore_timestamp,
                    backup_media=conf.mode)

        elif conf.backup_media == 'cinder':
            LOG.info("Restoring cinder backup from glance. Volume ID: {0}, "
                     "timestamp: {1}".format(conf.cinder_vol_id,
                                             restore_timestamp))
            res.restore_cinder_by_glance(conf.cinder_vol_id, restore_timestamp)
        elif conf.backup_media == 'cindernative':
            LOG.info("Restoring cinder native backup. Volume ID {0}, Backup ID"
                     " {1}, timestamp: {2}".format(conf.cindernative_vol_id,
                                                   conf.cindernative_backup_id,
                                                   restore_timestamp))
            res.restore_cinder(conf.cindernative_vol_id,
                               conf.cindernative_backup_id,
                               restore_timestamp)
        elif conf.backup_media == 'cinderbrick':
            LOG.info("Restoring cinder backup using os-brick. Volume ID {0}, "
                     "timestamp: {1}".format(conf.cinderbrick_vol_id,
                                             restore_timestamp))
            self.engine.restore(
                hostname_backup_name=self.conf.hostname_backup_name,
                restore_resource=conf.cinderbrick_vol_id,
                overwrite=conf.overwrite,
                recent_to_date=restore_timestamp,
                backup_media=conf.mode)
        else:
            raise Exception("unknown backup type: %s" % conf.backup_media)
        return {}


class AdminJob(Job):

    def _validate(self):
        # no validation required in this job
        if not self.conf.remove_from_date and not self.conf.remove_older_than:
            raise ValueError("You need to provide to remove backup older "
                             "than this time. You can use --remove-older-than "
                             "or --remove-from-date")

    def execute(self):
        if self.conf.remove_from_date:
            timestamp = utils.date_to_timestamp(self.conf.remove_from_date)
        else:
            timestamp = datetime.datetime.now() - \
                datetime.timedelta(days=float(self.conf.remove_older_than))
            timestamp = int(time.mktime(timestamp.timetuple()))

        if self.conf.backup_media == 'cinder':
            old_backups = self.get_cinder_old_backups(
                timestamp,
                self.conf.cinder_vol_id
            )
            self.remove_backup_dirs(old_backups, self.conf.cinder_vol_id)
            return {}

        hostname_backup_name_set = set()

        if self.conf.backup_media == 'nova':
            if self.conf.project_id:
                instance_ids = self.engine.get_nova_tenant(
                    self.conf.project_id)
                for instance_id in instance_ids:
                    hostname_backup_name = os.path.join(
                        self.conf.hostname_backup_name, instance_id)
                    hostname_backup_name_set.add(hostname_backup_name)
            else:
                hostname_backup_name = os.path.join(
                    self.conf.hostname_backup_name,
                    self.conf.nova_inst_id)
                hostname_backup_name_set.add(hostname_backup_name)
        else:
            hostname_backup_name_set.add(self.conf.hostname_backup_name)

        for backup_name in hostname_backup_name_set:
            self.storage.remove_older_than(self.engine,
                                           timestamp,
                                           backup_name)
        return {}

    def get_cinder_old_backups(self, timestamp, cinder_vol_id):
        path_to_list = self.get_path_prefix(cinder_vol_id)

        old_backups = []
        backup_dirs = self.storage.listdir(path_to_list)
        for backup_dir in backup_dirs:
            if int(backup_dir) <= int(timestamp):
                old_backups.append(backup_dir)

        return old_backups

    def remove_backup_dirs(self, backups_to_remove, cinder_vol_id):
        path_prefix = self.get_path_prefix(cinder_vol_id)
        for backup_to_remove in backups_to_remove:
            path_to_remove = "{0}/{1}".format(path_prefix, backup_to_remove)
            LOG.info("Remove backup: {0}".format(path_to_remove))
            self.storage.rmtree(path_to_remove)

    def get_path_prefix(self, cinder_vol_id):
        if self.storage.type == 'swift':
            path_prefix = "{0}/{1}/{2}".format(
                self.storage.container,
                self.storage.segments,
                cinder_vol_id
            )
        elif self.storage.type in ['local', 'ssh', 's3']:
            path_prefix = "{0}/{1}".format(
                self.storage.storage_path,
                cinder_vol_id
            )
        else:
            path_prefix = ''
        return path_prefix


class ExecJob(Job):

    def _validate(self):
        if not self.conf.command:
            raise ValueError("--command option is required")

    def execute(self):
        if self.conf.command:
            LOG.info('Executing exec job. Command: {0}'
                     .format(self.conf.command))
            exec_cmd.execute(self.conf.command)
        else:
            LOG.warning(
                'No command info options were set. Exiting.')
        return {}


class ConsistencyCheckException(Exception):
    pass
