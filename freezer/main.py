'''
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
'''

from freezer.utils import (
    start_time, elapsed_time, set_backup_level, validate_any_args,
    check_backup_existance)
from freezer.swift import (
    get_client, get_containers_list, show_containers,
    check_container_existance, get_container_content, remove_obj_older_than,
    show_objects)
from freezer.backup import (
    backup_mode_fs, backup_mode_mongo, backup_mode_mysql)
from freezer.restore import restore_fs

import logging


def freezer_main(backup_args):
    '''
    Program Main Execution. This main function is a wrapper for most
    of the other functions. By calling main() the program execution start
    and the respective actions are taken. If you want only use the single
    function is probably better to not import main()
    '''

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

    if show_containers(backup_args):
        elapsed_time(today_start)
        return True

    # Check if the provided container already exists in swift.
    # If it doesn't exist a new one will be created along with the segments
    # container as container_segments
    backup_args = check_container_existance(backup_args)

    # Get the object list of the remote containers and store id in the
    # same dict passes as argument under the dict.remote_obj_list namespace
    backup_args = get_container_content(backup_args)

    if show_objects(backup_args):
        elapsed_time(today_start)
        return True

    # Check if a backup exist in swift with same name. If not, set
    # backup level to 0
    manifest_meta_dict = check_backup_existance(backup_args)

    # Set the right backup level for incremental backup
    (backup_args, manifest_meta_dict) = set_backup_level(
        backup_args, manifest_meta_dict)

    backup_args.manifest_meta_dict = manifest_meta_dict
    # File system backup mode selected
    if backup_args.mode == 'fs':
        # If any of the restore options was specified, then a data restore
        # will be executed
        if validate_any_args([
            backup_args.restore_from_date, backup_args.restore_from_host,
                backup_args.restore_abs_path]):
            logging.info('[*] Executing FS restore...')
            restore_fs(backup_args)
        else:
            backup_mode_fs(backup_args, time_stamp, manifest_meta_dict)
    elif backup_args.mode == 'mongo':
        backup_mode_mongo(backup_args, time_stamp, manifest_meta_dict)
    elif backup_args.mode == 'mysql':
        backup_mode_mysql(backup_args, time_stamp, manifest_meta_dict)
    else:
        logging.critical('[*] Error: Please provide a valid backup mode')
        raise ValueError

    remove_obj_older_than(backup_args)

    # Elapsed time:
    elapsed_time(today_start)
