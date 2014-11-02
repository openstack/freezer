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

Arguments and general parameters definitions
"""

import sys
import argparse
import distutils.spawn as distspawn
import os
import logging


def backup_arguments():
    """
    Default arguments and command line options interface. The function return
    a name space called backup_args.
    """
    arg_parser = argparse.ArgumentParser(prog='freezerc')
    arg_parser.add_argument(
        '--action', choices=['backup', 'restore', 'info', 'admin'],
        help=(
            "Set the action to be taken. backup and restore are"
            " self explanatory, info is used to retrieve info from the"
            " storage media, while maintenance is used to delete old backups"
            " and other admin actions. Default backup."),
        dest='action', default='backup')
    arg_parser.add_argument(
        '-F', '--path-to-backup', '--file-to-backup', action='store',
        help="The file or directory you want to back up to Swift",
        dest='src_file', default=False)
    arg_parser.add_argument(
        '-N', '--backup-name', action='store',
        help="The backup name you want to use to identify your backup \
        on Swift", dest='backup_name', default=False)
    arg_parser.add_argument(
        '-m', '--mode', action='store',
        help="Set the technology to back from. Options are, fs (filesystem),\
        mongo (MongoDB), mysql (MySQL). Default set to fs", dest='mode',
        default='fs')
    arg_parser.add_argument(
        '-C', '--container', action='store',
        help="The Swift container used to upload files to",
        dest='container', default='freezer_backups')
    arg_parser.add_argument(
        '-L', '--list-containers', action='store_true',
        help='''List the Swift containers on remote Object Storage Server''',
        dest='list_container', default=False)
    arg_parser.add_argument(
        '-l', '--list-objects', action='store_true',
        help='''List the Swift objects stored in a container on remote Object\
        Storage Server.''', dest='list_objects', default=False)
    arg_parser.add_argument(
        '-o', '--get-object', action='store',
        help="The Object name you want to download on the local file system.",
        dest='object', default=False)
    arg_parser.add_argument(
        '-d', '--dst-file', action='store',
        help="The file name used to save the object on your local disk and\
        upload file in swift", dest='dst_file', default=False)
    arg_parser.add_argument(
        '--lvm-auto-snap', action='store',
        help=("Automatically guess the volume group and volume name for "
              "given PATH."),
        dest='lvm_auto_snap',
        default=False)
    arg_parser.add_argument(
        '--lvm-srcvol', action='store',
        help="Set the lvm volume you want to take a snaphost from. Default\
        no volume", dest='lvm_srcvol', default=False)
    arg_parser.add_argument(
        '--lvm-snapname', action='store',
        help="Set the lvm snapshot name to use. If the snapshot name already\
        exists, the old one will be used a no new one will be created. Default\
        freezer_backup_snap.", dest='lvm_snapname', default=False)
    arg_parser.add_argument(
        '--lvm-snapsize', action='store',
        help="Set the lvm snapshot size when creating a new snapshot.\
            Please add G for Gigabytes or M for Megabytes, i.e. 500M or 8G.\
            Default 5G.", dest='lvm_snapsize', default=False)
    arg_parser.add_argument(
        '--lvm-dirmount', action='store',
        help="Set the directory you want to mount the lvm snapshot to.\
        Default not set", dest='lvm_dirmount', default=False)
    arg_parser.add_argument(
        '--lvm-volgroup', action='store',
        help="Specify the volume group of your logical volume.\
            This is important to mount your snapshot volume. Default not set",
        dest='lvm_volgroup', default=False)
    arg_parser.add_argument(
        '--max-level', action='store',
        help="Set the backup level used with tar to implement incremental \
        backup. If a level 1 is specified but no level 0 is already \
        available, a level 0 will be done and subesequently backs to level 1.\
        Default 0 (No Incremental)", dest='max_backup_level',
        type=int, default=False)
    arg_parser.add_argument(
        '--always-level', action='store', help="Set backup\
        maximum level used with tar to implement incremental backup. If a \
        level 3 is specified, the backup will be executed from level 0 to \
        level 3 and to that point always a backup level 3 will be executed. \
        It will not restart from level 0. This option has precedence over \
        --max-backup-level. Default False (Disabled)",
        dest='always_backup_level', type=int, default=False)
    arg_parser.add_argument(
        '--restart-always-level', action='store', help="Restart the backup \
        from level 0 after n days. Valid only if --always-level option \
        if set. If --always-level is used together with --remove-older-then, \
        there might be the chance where the initial level 0 will be removed \
        Default False (Disabled)",
        dest='restart_always_backup', type=float, default=False)
    arg_parser.add_argument(
        '-R', '--remove-older-then', action='store',
        help="Checks in the specified container for object older then the \
        specified days. If i.e. 30 is specified, it will remove the remote \
        object older than 30 days. Default False (Disabled)",
        dest='remove_older_than', type=float, default=False)
    arg_parser.add_argument(
        '--no-incremental', action='store_true',
        help='''Disable incremantal feature. By default freezer build the
        meta data even for level 0 backup. By setting this option incremental
        meta data is not created at all. Default disabled''',
        dest='no_incremental', default=False)
    arg_parser.add_argument(
        '--hostname', action='store',
        help='''Set hostname to execute actions. If you are executing freezer
        from one host but you want to delete objects belonging to another
        host then you can set this option that hostname and execute appropriate
        actions. Default current node hostname.''',
        dest='hostname', default=False)
    arg_parser.add_argument(
        '--mysql-conf', action='store',
        help='''Set the MySQL configuration file where freezer retrieve
        important information as db_name, user, password, host.
        Following is an example of config file:
        # cat ~/.freezer/backup_mysql_conf
        host     = <db-host>
        user     = <mysqluser>
        password = <mysqlpass>''',
        dest='mysql_conf_file', default=False)
    arg_parser.add_argument(
        '--log-file', action='store',
        help='Set log file. By default logs to /var/log/freezer.log',
        dest='log_file', default='/var/log/freezer.log')
    arg_parser.add_argument(
        '--exclude', action='store', help="Exclude files,\
        given as a PATTERN.Ex: --exclude '*.log' will exclude any file with \
        name ending with .log. Default no exclude", dest='exclude',
        default=False)
    arg_parser.add_argument(
        '--dereference-symlink', choices=['none', 'soft', 'hard', 'all'],
        help=(
            "Follow hard and soft links and archive and dump the files they "
            " refer to. Default False."),
        dest='dereference_symlink', default='none')
    arg_parser.add_argument(
        '-U', '--upload', action='store_true',
        help="Upload to Swift the destination file passed to the -d option.\
            Default upload the data", dest='upload', default=True)
    arg_parser.add_argument(
        '--encrypt-pass-file', action='store',
        help="Passing a private key to this option, allow you to encrypt the \
            files before to be uploaded in Swift. Default do not encrypt.",
        dest='encrypt_pass_file', default=False)
    arg_parser.add_argument(
        '-M', '--max-segment-size', action='store',
        help="Set the maximum file chunk size in bytes to upload to swift\
        Default 67108864 bytes (64MB)",
        dest='max_seg_size', type=int, default=67108864)
    arg_parser.add_argument(
        '--restore-abs-path', action='store',
        help=('Set the absolute path where you want your data restored. '
              'Default False.'),
        dest='restore_abs_path', default=False)
    arg_parser.add_argument(
        '--restore-from-host', action='store',
        help='''Set the hostname used to identify the data you want to restore
        from. If you want to restore data in the same host where the backup
        was executed just type from your shell: "$ hostname" and the output is
        the value that needs to be passed to this option. Mandatory with
        Restore Default False.''', dest='restore_from_host', default=False)
    arg_parser.add_argument(
        '--restore-from-date', action='store',
        help='''Set the absolute path where you want your data restored.
        Please provide datime in forma "YYYY-MM-DDThh:mm:ss"
        i.e. "1979-10-03T23:23:23". Make sure the "T" is between date and time
        Default False.''', dest='restore_from_date', default=False)
    arg_parser.add_argument(
        '--max-priority', action='store_true',
        help='''Set the cpu process to the highest priority (i.e. -20 on Linux)
        and real-time for I/O. The process priority will be set only if nice
        and ionice are installed Default disabled. Use with caution.''',
        dest='max_priority', default=False)
    arg_parser.add_argument(
        '-V', '--version', action='store_true',
        help='''Print the release version and exit''',
        dest='version', default=False)

    backup_args = arg_parser.parse_args()
    # Set additional namespace attributes
    backup_args.__dict__['remote_match_backup'] = []
    backup_args.__dict__['remote_objects'] = []
    backup_args.__dict__['remote_obj_list'] = []
    backup_args.__dict__['remote_newest_backup'] = u''
    # Set default workdir to ~/.freezer
    backup_args.__dict__['workdir'] = os.path.expanduser(u'~/.freezer')
    # Create a new namespace attribute for container_segments
    backup_args.__dict__['container_segments'] = u'{0}_segments'.format(
        backup_args.container)

    # The containers used by freezer to executed backups needs to have
    # freezer_ prefix in the name. If the user provider container doesn't
    # have the prefix, it is automatically added also to the container
    # segments name. This is done to quickly identify the containers
    # that contain freezer generated backups
    if not backup_args.container.startswith('freezer_'):
        backup_args.container = 'freezer_{0}'.format(
            backup_args.container)
        backup_args.container_segments = 'freezer_{0}'.format(
            backup_args.container_segments)

    # If hostname is not set, hostname of the current node will be used
    if not backup_args.hostname:
        backup_args.__dict__['hostname'] = os.uname()[1]
    backup_args.__dict__['manifest_meta_dict'] = {}
    backup_args.__dict__['curr_backup_level'] = ''
    backup_args.__dict__['manifest_meta_dict'] = ''
    backup_args.__dict__['tar_path'] = distspawn.find_executable('tar')
    # If freezer is being used under OSX, please install gnutar and
    # rename the executable as gnutar
    if 'darwin' in sys.platform or 'bsd' in sys.platform:
        if distspawn.find_executable('gtar'):
            backup_args.__dict__['tar_path'] = \
                distspawn.find_executable('gtar')
        else:
            logging.critical('[*] Please install gnu tar (gtar) as it is a \
                mandatory requirement to use freezer.')
            raise Exception

    # Get absolute path of other commands used by freezer
    backup_args.__dict__['lvcreate_path'] = distspawn.find_executable(
        'lvcreate')
    backup_args.__dict__['lvremove_path'] = distspawn.find_executable(
        'lvremove')
    backup_args.__dict__['bash_path'] = distspawn.find_executable('bash')
    backup_args.__dict__['openssl_path'] = distspawn.find_executable('openssl')
    backup_args.__dict__['file_path'] = distspawn.find_executable('file')
    backup_args.__dict__['mount_path'] = distspawn.find_executable('mount')
    backup_args.__dict__['umount_path'] = distspawn.find_executable('umount')
    backup_args.__dict__['ionice'] = distspawn.find_executable('ionice')

    # MySQLdb object
    backup_args.__dict__['mysql_db_inst'] = ''

    # Freezer version
    backup_args.__dict__['__version__'] = '1.1.0'

    return backup_args, arg_parser
