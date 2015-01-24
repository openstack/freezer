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

Freezer main execution function
"""

from freezer import swift
from freezer import utils
from freezer import backup
from freezer import restore

import logging


def freezer_main(backup_args):
    """Freezer Main execution function.
    This main function is a wrapper for most
    of the other functions. By calling main() the program execution start
    and the respective actions are taken. If you want only use the single
    function is probably better to not import main()
    """

    # Computing execution start datetime and Timestamp
    (time_stamp, today_start) = utils.start_time()
    # Add timestamp to the arguments namespace
    backup_args.__dict__['time_stamp'] = time_stamp

    # Initialize the swift connector and store it in the same dict passed
    # as argument under the dict.sw_connector namespace. This is helpful
    # so the swift client object doesn't need to be initialized every time
    backup_args = swift.get_client(backup_args)

    # Get the list of the containers
    backup_args = swift.get_containers_list(backup_args)

    if backup_args.action == 'info' or backup_args.list_container or \
            backup_args.list_objects:
        if backup_args.list_container:
            swift.show_containers(backup_args)
        elif backup_args.list_objects:
            containers = swift.check_container_existance(backup_args)
            if containers['main_container'] is not True:
                logging.critical(
                    '[*] Container {0} not available'.format(
                        backup_args.container))
                return False
            backup_args = swift.get_container_content(backup_args)
            swift.show_objects(backup_args)
        else:
            logging.warning(
                '[*] No retrieving info options were set. Exiting.')
            utils.elapsed_time(today_start)
            return False
        utils.elapsed_time(today_start)
        return True

    if backup_args.action == 'restore':
        logging.info('[*] Executing FS restore...')

        # Check if the provided container already exists in swift.
        containers = swift.check_container_existance(backup_args)
        if containers['main_container'] is not True:
            raise ValueError('Container: {0} not found. Please provide an '
                             'existing container.'
                             .format(backup_args.container))

        # Get the object list of the remote containers and store it in the
        # same dict passes as argument under the dict.remote_obj_list namespace
        backup_args = swift.get_container_content(backup_args)
        restore.restore_fs(backup_args)

    if backup_args.action == 'backup':
        # Check if the provided container already exists in swift.
        containers = swift.check_container_existance(backup_args)

        if containers['main_container'] is not True:
            swift.create_containers(backup_args)

        # Get the object list of the remote containers and store it in the
        # same dict passes as argument under the dict.remote_obj_list namespace
        backup_args = swift.get_container_content(backup_args)

        # Check if a backup exist in swift with same name. If not, set
        # backup level to 0
        manifest_meta_dict = utils.check_backup_existance(backup_args)

        # Set the right backup level for incremental backup
        (backup_args, manifest_meta_dict) = utils.set_backup_level(
            backup_args, manifest_meta_dict)

        backup_args.manifest_meta_dict = manifest_meta_dict
        # File system backup mode selected
        if backup_args.mode == 'fs':
            backup.backup_mode_fs(
                backup_args, time_stamp, manifest_meta_dict)
        elif backup_args.mode == 'mongo':
            backup.backup_mode_mongo(
                backup_args, time_stamp, manifest_meta_dict)
        elif backup_args.mode == 'mysql':
            backup.backup_mode_mysql(
                backup_args, time_stamp, manifest_meta_dict)
        else:
            raise ValueError('Please provide a valid backup mode')

    # Admin tasks code should go here, before moving it on a dedicated module
    if backup_args.action == 'admin' or backup_args.remove_older_than:
        # Remove backups older if set.
        backup_args = swift.get_container_content(backup_args)
        swift.remove_obj_older_than(backup_args)

    # Compute elapsed time
    utils.elapsed_time(today_start)
