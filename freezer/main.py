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

from freezer.utils import (
    start_time, elapsed_time, set_backup_level,
    check_backup_existance)
from freezer.swift import (
    get_client, get_containers_list, show_containers,
    check_container_existance, get_container_content, remove_obj_older_than,
    show_objects, create_containers)
from freezer.backup import (
    backup_mode_fs, backup_mode_mongo, backup_mode_mysql)
from freezer.restore import restore_fs

import logging


def freezer_main(backup_args):
    """Freezer Main execution function.
    This main function is a wrapper for most
    of the other functions. By calling main() the program execution start
    and the respective actions are taken. If you want only use the single
    function is probably better to not import main()
    """

    # Computing execution start datetime and Timestamp
    (time_stamp, today_start) = start_time()
    # Add timestamp to the arguments namespace
    backup_args.__dict__['time_stamp'] = time_stamp

    # Initialize the swift connector and store it in the same dict passed
    # as argument under the dict.sw_connector namespace. This is helpful
    # so the swift client object doesn't need to be initialized every time
    backup_args = get_client(backup_args)

    # Get the list of the containers
    backup_args = get_containers_list(backup_args)

    if backup_args.action == 'info' or backup_args.list_container or \
            backup_args.list_objects:
        if backup_args.list_container:
            show_containers(backup_args)
        elif backup_args.list_objects:
            containers = check_container_existance(backup_args)
            if containers['main_container'] is not True:
                logging.critical(
                    '[*] Container {0} not available'.format(
                        backup_args.container))
                return False
            backup_args = get_container_content(backup_args)
            show_objects(backup_args)
        else:
            logging.warning(
                '[*] No retrieving info options were set. Exiting.')
            elapsed_time(today_start)
            return False

        elapsed_time(today_start)
        return True

    if backup_args.action == 'restore':
        logging.info('[*] Executing FS restore...')

        # Check if the provided container already exists in swift.
        containers = check_container_existance(backup_args)
        if containers['main_container'] is not True:
            exc_msg = ('[*] Container: {0} not found. Please provide an '
                       'existing container.'.format(backup_args.container))
            logging.critical(exc_msg)
            raise ValueError(exc_msg)

        # Get the object list of the remote containers and store it in the
        # same dict passes as argument under the dict.remote_obj_list namespace
        backup_args = get_container_content(backup_args)
        restore_fs(backup_args)

    if backup_args.action == 'backup':
        # Check if the provided container already exists in swift.
        containers = check_container_existance(backup_args)

        if containers['main_container'] is not True:
            create_containers(backup_args)

        # Get the object list of the remote containers and store it in the
        # same dict passes as argument under the dict.remote_obj_list namespace
        backup_args = get_container_content(backup_args)

        # Check if a backup exist in swift with same name. If not, set
        # backup level to 0
        manifest_meta_dict = check_backup_existance(backup_args)

        # Set the right backup level for incremental backup
        (backup_args, manifest_meta_dict) = set_backup_level(
            backup_args, manifest_meta_dict)

        backup_args.manifest_meta_dict = manifest_meta_dict
        # File system backup mode selected
        if backup_args.mode == 'fs':
            backup_mode_fs(backup_args, time_stamp, manifest_meta_dict)
        elif backup_args.mode == 'mongo':
            backup_mode_mongo(backup_args, time_stamp, manifest_meta_dict)
        elif backup_args.mode == 'mysql':
            backup_mode_mysql(backup_args, time_stamp, manifest_meta_dict)
        else:
            logging.critical('[*] Error: Please provide a valid backup mode')
            raise ValueError

    # Admin tasks code should go here, before moving it on a dedicated module
    if backup_args.action == 'admin' or backup_args.remove_older_than:
        # Remove backups older if set.
        remove_obj_older_than(backup_args)

    # Compute elapsed time
    elapsed_time(today_start)
