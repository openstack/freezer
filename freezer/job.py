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
"""

from freezer import swift
from freezer import utils
from freezer import backup
from freezer import restore

import logging


class Job:
    def __init__(self, conf_dict):
        self.conf = conf_dict

    def execute(self):
        logging.info('[*] Action not implemented')

    @staticmethod
    def executemethod(func):
        def wrapper(self):
            self.start_time = utils.DateTime.now()
            self.conf.time_stamp = self.start_time.timestamp
            logging.info('[*] Job execution Started at: {0}'.
                         format(self.start_time))

            self.conf = swift.get_client(self.conf)
            self.conf = swift.get_containers_list(self.conf)
            retval = func(self)

            end_time = utils.DateTime.now()
            logging.info('[*] Job execution Finished, at: {0}'.
                         format(end_time))
            logging.info('[*] Job time Elapsed: {0}'.
                         format(end_time - self.start_time))
            return retval
        return wrapper


class InfoJob(Job):
    @Job.executemethod
    def execute(self):
        if self.conf.list_container:
            swift.show_containers(self.conf)
        elif self.conf.list_objects:
            containers = swift.check_container_existance(self.conf)
            if containers['main_container'] is not True:
                logging.critical(
                    '[*] Container {0} not available'.format(
                        self.conf.container))
                return False
            self.conf = swift.get_container_content(self.conf)
            swift.show_objects(self.conf)
        else:
            logging.warning(
                '[*] No retrieving info options were set. Exiting.')
            return False
        return True


class BackupJob(Job):
    @Job.executemethod
    def execute(self):
        containers = swift.check_container_existance(self.conf)

        if containers['main_container'] is not True:
            swift.create_containers(self.conf)

        if self.conf.no_incremental:
            if self.conf.max_backup_level or \
               self.conf.always_backup_level:
                raise Exception(
                    'no-incremental option is not compatible '
                    'with backup level options')
            manifest_meta_dict = {}
        else:
            # Get the object list of the remote containers
            # and store it in self.conf.remote_obj_list
            self.conf = swift.get_container_content(self.conf)

            # Check if a backup exist in swift with same name.
            # If not, set backup level to 0
            manifest_meta_dict =\
                utils.check_backup_and_tar_meta_existence(self.conf)

        (self.conf, manifest_meta_dict) = utils.set_backup_level(
            self.conf, manifest_meta_dict)

        self.conf.manifest_meta_dict = manifest_meta_dict

        if self.conf.mode == 'fs':
            backup.backup_mode_fs(
                self.conf, self.start_time.timestamp, manifest_meta_dict)
        elif self.conf.mode == 'mongo':
            backup.backup_mode_mongo(
                self.conf, self.start_time.timestamp, manifest_meta_dict)
        elif self.conf.mode == 'mysql':
            backup.backup_mode_mysql(
                self.conf, self.start_time.timestamp, manifest_meta_dict)
        else:
            raise ValueError('Please provide a valid backup mode')


class RestoreJob(Job):
    @Job.executemethod
    def execute(self):
        logging.info('[*] Executing FS restore...')

        # Check if the provided container already exists in swift.
        containers = swift.check_container_existance(self.conf)
        if containers['main_container'] is not True:
            raise ValueError('Container: {0} not found. Please provide an '
                             'existing container.'
                             .format(self.conf.container))

        # Get the object list of the remote containers and store it in the
        # same dict passes as argument under the dict.remote_obj_list namespace
        self.conf = swift.get_container_content(self.conf)
        restore.restore_fs(self.conf)


class AdminJob(Job):
    @Job.executemethod
    def execute(self):
        self.conf = swift.get_container_content(self.conf)
        swift.remove_obj_older_than(self.conf)


def create_job(conf):
    if conf.action == 'backup':
        return BackupJob(conf)
    if conf.action == 'restore':
        return RestoreJob(conf)
    if conf.action == 'info':
        return InfoJob(conf)
    if conf.action == 'admin':
        return AdminJob(conf)
    raise Exception('Action "{0}" not supported'.format(conf.action))
