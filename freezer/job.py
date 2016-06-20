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

    def execute(self):
        start_time = utils.DateTime.now()
        LOG.info('Job execution Started at: {0}'.format(start_time))
        retval = self.execute_method()
        end_time = utils.DateTime.now()
        LOG.info('Job execution Finished, at: {0}'.format(end_time))
        LOG.info('Job time Elapsed: {0}'.format(end_time - start_time))
        return retval

    @abc.abstractmethod
    def execute_method(self):
        pass


class InfoJob(Job):
    def execute_method(self):
        self.storage.info()


class BackupJob(Job):
    def execute_method(self):
        try:
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
        backup_instance = self.backup(app_mode)

        level = backup_instance.level if backup_instance else 0

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
            app_mode.prepare()
            snapshot_taken = snapshot.snapshot_create(self.conf)
            if snapshot_taken:
                app_mode.release()
            try:
                filepath = '.'
                chdir_path = os.path.expanduser(
                    os.path.normpath(self.conf.path_to_backup.strip()))

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

                hostname_backup_name = self.conf.hostname_backup_name
                backup_instance = self.storage.create_backup(
                    hostname_backup_name,
                    self.conf.no_incremental,
                    self.conf.max_level,
                    self.conf.always_level,
                    self.conf.restart_always_level,
                    time_stamp=time_stamp)
                self.engine.backup(filepath, backup_instance)
                return backup_instance
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
            LOG.info('Executing nova backup')
            backup_os.backup_nova(self.conf.nova_inst_id)
        elif backup_media == 'cindernative':
            LOG.info('Executing cinder backup')
            backup_os.backup_cinder(self.conf.cindernative_vol_id)
        elif backup_media == 'cinder':
            LOG.info('Executing cinder snapshot')
            backup_os.backup_cinder_by_glance(self.conf.cinder_vol_id)
        else:
            raise Exception('unknown parameter backup_media %s' % backup_media)
        return None


class RestoreJob(Job):

    def execute_method(self):
        conf = self.conf
        LOG.info('Executing FS restore...')
        restore_timestamp = None

        restore_abs_path = conf.restore_abs_path
        if conf.restore_from_date:
            restore_timestamp = utils.date_to_timestamp(conf.restore_from_date)
        if conf.backup_media == 'fs':
            backup = self.storage.find_one(conf.hostname_backup_name,
                                           restore_timestamp)
            self.engine.restore(backup, restore_abs_path, conf.overwrite)

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
            res.restore_nova(conf.nova_inst_id, restore_timestamp)
        elif conf.backup_media == 'cinder':
            res.restore_cinder_by_glance(conf.cinder_vol_id, restore_timestamp)
        elif conf.backup_media == 'cindernative':
            res.restore_cinder(conf.cindernative_vol_id, restore_timestamp)
        else:
            raise Exception("unknown backup type: %s" % conf.backup_media)
        return {}


class ConsistencyCheckException(Exception):
    pass


class AdminJob(Job):

    def execute_method(self):
        if self.conf.remove_from_date:
            timestamp = utils.date_to_timestamp(self.conf.remove_from_date)
        else:
            timestamp = datetime.datetime.now() - \
                datetime.timedelta(days=self.conf.remove_older_than)
            timestamp = int(time.mktime(timestamp.timetuple()))

        self.storage.remove_older_than(timestamp,
                                       self.conf.hostname_backup_name)
        return {}


class ExecJob(Job):

    def execute_method(self):
        LOG.info('exec job....')
        if self.conf.command:
            LOG.info('Executing exec job....')
            exec_cmd.execute(self.conf.command)
        else:
            LOG.warning(
                'No command info options were set. Exiting.')
        return {}
