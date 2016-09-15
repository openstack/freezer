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
import six
import sys
import time

from freezer.openstack import backup
from freezer.openstack import restore
from freezer.snapshot import snapshot
from freezer.utils.checksum import CheckSum
from freezer.utils import exec_cmd
from freezer.utils import utils

from oslo_config import cfg
from oslo_log import log
from oslo_utils import importutils

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
        self.storage.info()


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

    def execute(self):
        LOG.info('Backup job started. '
                 'backup_name: {0}, container: {1}, hostname: {2}, mode: {3},'
                 ' Storage: {4}, compression: {5}'
                 .format(self.conf.backup_name, self.conf.container,
                         self.conf.hostname, self.conf.mode, self.conf.storage,
                         self.conf.compression))
        try:
            if self.conf.mode is 'fs':
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
                    ignorelinks = (self.conf.dereference_symlink == 'none' or
                                   self.conf.dereference_symlink == 'hard')
                    consistency_checksum = CheckSum(
                        filepath, ignorelinks=ignorelinks).compute()
                    LOG.info('Computed checksum for consistency {0}'.
                             format(consistency_checksum))
                    self.conf.consistency_checksum = consistency_checksum

                return self.engine.backup(
                    backup_path=filepath,
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
            LOG.info('Executing nova backup. Instance ID: {0}'.format(
                self.conf.nova_inst_id))
            backup_os.backup_nova(self.conf.nova_inst_id)
        elif backup_media == 'cindernative':
            LOG.info('Executing cinder native backup. Volume ID: {0}, '
                     'incremental: {1}'.format(self.conf.cindernative_vol_id,
                                               self.conf.incremental))
            backup_os.backup_cinder(self.conf.cindernative_vol_id,
                                    incremental=self.conf.incremental)
        elif backup_media == 'cinder':
            LOG.info('Executing cinder snapshot. Volume ID: {0}'.format(
                self.conf.cinder_vol_id))
            backup_os.backup_cinder_by_glance(self.conf.cinder_vol_id)
        else:
            raise Exception('unknown parameter backup_media %s' % backup_media)
        return None


class RestoreJob(Job):

    def _validate(self):
        if not self.conf.restore_abs_path and not self.conf.nova_inst_id \
                and not self.conf.cinder_vol_id and not \
                self.conf.cindernative_vol_id:
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
        LOG.info('Executing FS restore...')
        restore_timestamp = None

        restore_abs_path = conf.restore_abs_path
        if conf.restore_from_date:
            restore_timestamp = utils.date_to_timestamp(conf.restore_from_date)
        if conf.backup_media == 'fs':
            self.engine.restore(
                hostname_backup_name=self.conf.hostname_backup_name,
                restore_path=restore_abs_path,
                overwrite=conf.overwrite,
                recent_to_date=conf.restore_from_date)

            try:
                if conf.consistency_checksum:
                    backup_checksum = conf.consistency_checksum
                    restore_checksum = CheckSum(restore_abs_path,
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
        res = restore.RestoreOs(conf.client_manager, conf.container)
        if conf.backup_media == 'nova':
            LOG.info("Restoring nova backup. Instance ID: {0}, timestamp: {1}"
                     .format(conf.nova_inst_id, restore_timestamp))
            nova_network = None
            if conf.nova_restore_network:
                nova_network = conf.nova_restore_network
            res.restore_nova(conf.nova_inst_id, restore_timestamp,
                             nova_network)
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
                datetime.timedelta(days=self.conf.remove_older_than)
            timestamp = int(time.mktime(timestamp.timetuple()))

        self.storage.remove_older_than(self.engine,
                                       timestamp,
                                       self.conf.hostname_backup_name)
        return {}


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
