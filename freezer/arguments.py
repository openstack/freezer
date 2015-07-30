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
import os
import argparse

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import logging
from distutils import spawn as distspawn
import utils
import socket

from freezer.winutils import is_windows
from os.path import expanduser

home = expanduser("~")


DEFAULT_PARAMS = {
    'os_auth_ver': 2, 'list_objects': False, 'get_object': False,
    'lvm_auto_snap': False, 'lvm_volgroup': False,
    'exclude': False, 'sql_server_conf': False,
    'backup_name': False, 'quiet': False,
    'container': 'freezer_backups', 'no_incremental': False,
    'max_segment_size': 67108864, 'lvm_srcvol': False,
    'download_limit': -1, 'hostname': False, 'remove_from_date': False,
    'restart_always_level': False, 'lvm_dirmount': False,
    'dst_file': False, 'dereference_symlink': 'none',
    'restore_from_host': False, 'config': False, 'mysql_conf': False,
    'insecure': False, 'lvm_snapname': False, 'lvm_snapperm': 'ro',
    'max_priority': False, 'max_level': False, 'path_to_backup': False,
    'encrypt_pass_file': False, 'volume': False, 'proxy': False,
    'cinder_vol_id': '', 'cindernative_vol_id': '',
    'nova_inst_id': '', 'list_containers': False,
    'remove_older_than': None, 'restore_from_date': False,
    'upload_limit': -1, 'always_level': False, 'version': False,
    'dry_run': False, 'lvm_snapsize': False,
    'restore_abs_path': False, 'log_file': None,
    'upload': True, 'mode': 'fs', 'action': 'backup',
    'vssadmin': True, 'shadow': '', 'shadow_path': '',
    'windows_volume': '', 'command': None, 'metadata_out': False,
    'storage': 'swift', 'ssh_key': '', 'ssh_username': '', 'ssh_host': ''}


def alter_proxy(args_dict):
    """
    Read proxy option from dictionary and alter the HTTP_PROXY and/or
    HTTPS_PROXY system variables
    """
    # Default case where 'proxy' key is not set -- do nothing
    if args_dict['proxy'] is False:
        return
    proxy_value = args_dict['proxy'].lower()
    # python-swift client takes into account both
    # upper and lower case proxies so clear them all
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    if proxy_value == '':
        pass
    elif proxy_value.startswith('http://') or \
            proxy_value.startswith('https://'):
        logging.info('[*] Using proxy {0}'.format(proxy_value))
        os.environ['HTTP_PROXY'] = str(proxy_value)
        os.environ['HTTPS_PROXY'] = str(proxy_value)
    else:
        raise Exception('Proxy has unknown scheme')


def backup_arguments(args_dict={}):
    """
    Default arguments and command line options interface. The function return
    a name space called backup_args.
    """

    conf_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False, prog='freezerc')

    conf_parser.add_argument(
        '--config', action='store', dest='config', default=False,
        help=("Config file abs path. Option arguments are provided "
              "from config file. When config file is used any option "
              "from command line provided take precedence."))

    defaults = DEFAULT_PARAMS.copy()
    args, remaining_argv = conf_parser.parse_known_args()
    if args.config:
        config = configparser.SafeConfigParser()
        config.read([args.config])
        section = config.sections()[0]
        for option in config.options(section):
            option_value = config.get(section, option)
            if option_value in ('False', 'None'):
                option_value = False
            defaults[option] = option_value

    # Generate a new argparse istance and inherit options from config parse
    arg_parser = argparse.ArgumentParser(
        parents=[conf_parser])

    arg_parser.add_argument(
        '--action', choices=['backup', 'restore', 'info', 'admin',
                             'exec'],
        help=(
            "Set the action to be taken. backup and restore are"
            " self explanatory, info is used to retrieve info from the"
            " storage media, exec is used to execute a script,"
            " while admin is used to delete old backups"
            " and other admin actions. Default backup."),
        dest='action', default='backup')
    arg_parser.add_argument(
        '-F', '--path-to-backup', '--file-to-backup', action='store',
        help="The file or directory you want to back up to Swift",
        dest='path_to_backup', default=False)
    arg_parser.add_argument(
        '-N', '--backup-name', action='store',
        help="The backup name you want to use to identify your backup \
        on Swift", dest='backup_name', default=False)
    arg_parser.add_argument(
        '-m', '--mode', action='store',
        help="Set the technology to back from. Options are, fs (filesystem),\
        mongo (MongoDB), mysql (MySQL), sqlserver (SQL Server)\
        Default set to fs", dest='mode',
        default='fs')
    arg_parser.add_argument(
        '-C', '--container', action='store',
        help="The Swift container (or path to local storage) "
             "used to upload files to",
        dest='container', default='freezer_backups')
    arg_parser.add_argument(
        '-L', '--list-containers', action='store_true',
        help='''List the Swift containers on remote Object Storage Server''',
        dest='list_containers', default=False)
    arg_parser.add_argument(
        '-l', '--list-objects', action='store_true',
        help='''List the Swift objects stored in a container on remote Object\
        Storage Server.''', dest='list_objects', default=False)
    arg_parser.add_argument(
        '-o', '--get-object', action='store',
        help="The Object name you want to download on the local file system.",
        dest='get_object', default=False)
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
        '--lvm-snap-perm', action='store', choices=['ro', 'rw'],
        help="Set the lvm snapshot permission to use. If the permission\
        is set to ro The snapshot will be immutable - read only -.\
        If the permission is set to rw it will be mutable",
        dest='lvm_snapperm', default='ro')
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
        available, a level 0 will be done and subsequently backs to level 1.\
        Default 0 (No Incremental)", dest='max_level',
        type=int, default=False)
    arg_parser.add_argument(
        '--always-level', action='store', help="Set backup\
        maximum level used with tar to implement incremental backup. If a \
        level 3 is specified, the backup will be executed from level 0 to \
        level 3 and to that point always a backup level 3 will be executed. \
        It will not restart from level 0. This option has precedence over \
        --max-backup-level. Default False (Disabled)",
        dest='always_level', type=int, default=False)
    arg_parser.add_argument(
        '--restart-always-level', action='store', help="Restart the backup \
        from level 0 after n days. Valid only if --always-level option \
        if set. If --always-level is used together with --remove-older-then, \
        there might be the chance where the initial level 0 will be removed \
        Default False (Disabled)",
        dest='restart_always_level', type=float, default=False)
    arg_parser.add_argument(
        '-R', '--remove-older-then', '--remove-older-than', action='store',
        help=('Checks in the specified container for object older than the '
              'specified days.'
              'If i.e. 30 is specified, it will remove the remote object '
              'older than 30 days. Default False (Disabled) '
              'The option --remove-older-then is deprecated '
              'and will be removed soon'),
        dest='remove_older_than', type=float, default=None)
    arg_parser.add_argument(
        '--remove-from-date', action='store',
        help=('Checks the specified container and removes objects older than '
              'the provided datetime in the form "YYYY-MM-DDThh:mm:ss '
              'i.e. "1974-03-25T23:23:23". '
              'Make sure the "T" is between date and time '),
        dest='remove_from_date', default=False)
    arg_parser.add_argument(
        '--no-incremental', action='store_true',
        help='''Disable incremental feature. By default freezer build the
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
        important information as db_name, user, password, host, port.
        Following is an example of config file:
        # cat ~/.freezer/backup_mysql_conf
        host     = <db-host>
        user     = <mysqluser>
        password = <mysqlpass>
        port     = <db-port>''',
        dest='mysql_conf', default=False)
    arg_parser.add_argument(
        '--metadata-out', action='store',
        help=('Set the filename to which write the metadata regarding '
              'the backup metrics. Use "-" to output to standard output.'),
        dest='metadata_out', default=False)

    if is_windows():
        arg_parser.add_argument(
            '--log-file', action='store',
            help='Set log file. By default logs to ~/freezer.log',
            dest='log_file', default=os.path.join(home,
                                                  '.freezer',
                                                  'freezer.log'))
    else:
        arg_parser.add_argument(
            '--log-file', action='store',
            help='Set log file. By default logs to /var/log/freezer.log'
                 'If that file is not writable, freezer tries to log'
                 'to ~/.freezer/freezer.log',
            dest='log_file', default=None)
    arg_parser.add_argument(
        '--exclude', action='store', help="Exclude files,\
        given as a PATTERN.Ex: --exclude '*.log' will exclude any file \
        with name ending with .log. Default no exclude", dest='exclude',
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
        dest='max_segment_size', type=int, default=67108864)
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
        Please provide datetime in format "YYYY-MM-DDThh:mm:ss"
        i.e. "1979-10-03T23:23:23". Make sure the "T" is between date and time
        Default None.''', dest='restore_from_date', default=None)
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
    arg_parser.add_argument(
        '-q', '--quiet', action='store_true',
        help='''Suppress error messages''',
        dest='quiet', default=False)
    arg_parser.add_argument(
        '--insecure', action='store_true',
        help='Allow to access swift servers without checking SSL certs.',
        dest='insecure', default=False)
    arg_parser.add_argument(
        '--os-auth-ver', choices=['1', '2', '3'],
        action='store',
        help='Swift auth version, could be 1, 2 or 3',
        dest='os_auth_ver', default=2)
    arg_parser.add_argument(
        '--proxy', action='store',
        help='''Enforce proxy that alters system HTTP_PROXY and HTTPS_PROXY,
        use \'\' to eliminate all system proxies''',
        dest='proxy', default=False)
    arg_parser.add_argument(
        '--dry-run', action='store_true',
        help='Do everything except writing or removing objects',
        dest='dry_run', default=False)
    arg_parser.add_argument(
        '--upload-limit', action='store',
        help='''Upload bandwidth limit in Bytes per sec.
        Can be invoked with dimensions (10K, 120M, 10G).''',
        dest='upload_limit',
        type=utils.human2bytes,
        default=-1)
    arg_parser.add_argument(
        "--cinder-vol-id", action='store',
        help='Id of cinder volume for backup',
        dest="cinder_vol_id",
        default='')
    arg_parser.add_argument(
        "--nova-inst-id", action='store',
        help='Id of nova instance for backup',
        dest="nova_inst_id",
        default='')
    arg_parser.add_argument(
        "--cindernative-vol-id", action='store',
        help='Id of cinder volume for native backup',
        dest="cindernative_vol_id",
        default='')
    arg_parser.add_argument(
        '--download-limit', action='store',
        help='''Download bandwidth limit in Bytes per sec.
        Can be invoked with dimensions (10K, 120M, 10G).''',
        dest='download_limit',
        type=utils.human2bytes,
        default=-1)
    arg_parser.add_argument(
        '--sql-server-conf', action='store',
        help='''Set the SQL Server configuration file where freezer retrieve
        the sql server instance.
        Following is an example of config file:
        instance = <db-instance>''',
        dest='sql_server_conf', default=False)
    arg_parser.add_argument(
        '--vssadmin', action='store',
        help='''Create a backup using a snapshot on windows
        using vssadmin. Options are: True and False, default is True''',
        dest='vssadmin', default=True)
    arg_parser.add_argument(
        '--command', action='store',
        help='Command executed by exec action',
        dest='command', default=None)

    arg_parser.add_argument(
        '--storage', action='store',
        choices=['local', 'swift', 'ssh'],
        help="Storage for backups. Can be Swift or Local now. Swift is default"
             "storage now. Local stores backups on the same defined path and"
             "swift will store files in container.",
        dest='storage', default='swift')
    arg_parser.add_argument(
        '--ssh-key', action='store',
        help="Path ot ssh-key for ssh storage only",
        dest='ssh_key', default=DEFAULT_PARAMS['ssh_key'])
    arg_parser.add_argument(
        '--ssh-username', action='store',
        help="Remote username for ssh storage only",
        dest='ssh_username', default=DEFAULT_PARAMS['ssh_username'])
    arg_parser.add_argument(
        '--ssh-host', action='store',
        help="Remote host for ssh storage only",
        dest='ssh_host', default=DEFAULT_PARAMS['ssh_host'])

    arg_parser.set_defaults(**defaults)
    backup_args = arg_parser.parse_args()

    # windows bin
    path_to_binaries = os.path.dirname(os.path.abspath(__file__))

    # Intercept command line arguments if you are not using the CLIvss
    if args_dict:
        backup_args.__dict__.update(args_dict)

    # Set additional namespace attributes
    backup_args.__dict__['remote_match_backup'] = []
    backup_args.__dict__['remote_obj_list'] = []
    backup_args.__dict__['remote_newest_backup'] = u''
    # Set default workdir to ~/.freezer
    backup_args.__dict__['work_dir'] = os.path.join(home, '.freezer')

    # The containers used by freezer to executed backups needs to have
    # freezer_ prefix in the name. If the user provider container doesn't
    # have the prefix, it is automatically added also to the container
    # segments name. This is done to quickly identify the containers
    # that contain freezer generated backups
    if not backup_args.container.startswith('freezer_') and \
            backup_args.storage == 'swift':
        backup_args.container = 'freezer_{0}'.format(
            backup_args.container)

    # If hostname is not set, hostname of the current node will be used
    if not backup_args.hostname:
        backup_args.__dict__['hostname'] = socket.gethostname()
    backup_args.__dict__['manifest_meta_dict'] = {}
    backup_args.__dict__['curr_backup_level'] = ''
    backup_args.__dict__['manifest_meta_dict'] = ''
    if is_windows():
        backup_args.__dict__['tar_path'] = '{0}\\bin\\tar.exe'. \
            format(path_to_binaries)
    else:
        backup_args.__dict__['tar_path'] = distspawn.find_executable('tar')
    # If freezer is being used under OSX, please install gnutar and
    # rename the executable as gnutar
    if 'darwin' in sys.platform or 'bsd' in sys.platform:
        if distspawn.find_executable('gtar'):
            backup_args.__dict__['tar_path'] = \
                distspawn.find_executable('gtar')
        elif distspawn.find_executable('gnutar'):
            backup_args.__dict__['tar_path'] = \
                distspawn.find_executable('gnutar')
        else:
            raise Exception('Please install gnu tar (gtar) as it is a '
                            'mandatory requirement to use freezer.')

    # If we have provided --proxy then overwrite the system HTTP_PROXY and
    # HTTPS_PROXY
    alter_proxy(backup_args.__dict__)

    # Get absolute path of other commands used by freezer
    backup_args.__dict__['lvcreate_path'] = distspawn.find_executable(
        'lvcreate')
    backup_args.__dict__['lvremove_path'] = distspawn.find_executable(
        'lvremove')
    backup_args.__dict__['bash_path'] = distspawn.find_executable('bash')
    if is_windows():
        backup_args.__dict__['openssl_path'] = 'openssl'
    else:
        backup_args.__dict__['openssl_path'] = \
            distspawn.find_executable('openssl')
    backup_args.__dict__['file_path'] = distspawn.find_executable('file')
    backup_args.__dict__['mount_path'] = distspawn.find_executable('mount')
    backup_args.__dict__['umount_path'] = distspawn.find_executable('umount')
    backup_args.__dict__['ionice'] = distspawn.find_executable('ionice')

    # MySQLdb object
    backup_args.__dict__['mysql_db_inst'] = ''

    # SQL Server object
    backup_args.__dict__['sql_server_instance'] = ''

    # Windows volume
    backup_args.__dict__['shadow'] = ''
    backup_args.__dict__['shadow_path'] = ''
    backup_args.__dict__['file_name'] = ''
    if is_windows():
        if backup_args.path_to_backup:
            backup_args.__dict__['windows_volume'] = \
                backup_args.path_to_backup[:3]

        if backup_args.vssadmin == 'False' or backup_args.vssadmin == 'false':
            backup_args.vssadmin = False

    backup_args.__dict__['meta_data'] = {}
    backup_args.__dict__['meta_data_file'] = ''
    backup_args.__dict__['absolute_path'] = ''

    # Freezer version
    backup_args.__dict__['__version__'] = '1.1.3'

    # todo(enugaev) move it to new command line param backup_media
    backup_media = 'fs'
    if backup_args.cinder_vol_id:
        backup_media = 'cinder'
    elif backup_args.cindernative_vol_id:
        backup_media = 'cindernative'
    elif backup_args.nova_inst_id:
        backup_media = 'nova'

    backup_args.__dict__['backup_media'] = backup_media

    return backup_args, arg_parser
