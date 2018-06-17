# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

from distutils import spawn as distspawn
import os
import socket
import sys
import tempfile

from oslo_config import cfg
from oslo_config.cfg import NoSuchOptError
from oslo_log import log
from oslo_utils import encodeutils

from freezer import __version__ as FREEZER_VERSION
from freezer.utils import config as freezer_config
from freezer.utils import utils
from freezer.utils import winutils

CONF = cfg.CONF
LOG = log.getLogger(__name__)

home = os.path.expanduser("~")

DEFAULT_LVM_SNAPSIZE = '1G'
DEFAULT_LVM_MOUNT_BASEDIR = '/var/lib/freezer'
DEFAULT_LVM_SNAP_BASENAME = 'freezer_backup_snap'
DEFAULT_SSH_PORT = 22

_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                       'qpid=WARN', 'stevedore=WARN', 'oslo_log=INFO',
                       'iso8601=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystoneauth1=WARN', 'freezer=INFO']

_DEFAULT_LOGGING_CONTEXT_FORMAT = (
    '%(asctime)s.%(msecs)03d %(process)d '
    '%(levelname)s %(name)s [%(request_id)s '
    '%(user_identity)s] %(instance)s'
    '%(message)s')

DEFAULT_PARAMS = {
    'os_identity_api_version': None,
    'lvm_auto_snap': None, 'lvm_volgroup': None,
    'exclude': None, 'sql_server_conf': False,
    'backup_name': None, 'quiet': False,
    'container': 'freezer_backups', 'no_incremental': None,
    'max_segment_size': 33554432, 'lvm_srcvol': None,
    'download_limit': -1, 'hostname': None, 'remove_from_date': None,
    'restart_always_level': False, 'lvm_dirmount': None,
    'dereference_symlink': None,
    'config': None, 'mysql_conf': False,
    'insecure': False, 'lvm_snapname': None,
    'lvm_snapperm': 'ro', 'snapshot': None,
    'max_priority': None, 'max_level': False, 'path_to_backup': None,
    'encrypt_pass_file': None, 'volume': None, 'proxy': None,
    'cinder_vol_id': '', 'cindernative_vol_id': '',
    'cinderbrick_vol_id': '',
    'nova_inst_id': '', '__version__': FREEZER_VERSION,
    'remove_older_than': None, 'restore_from_date': None,
    'upload_limit': -1, 'always_level': False, 'version': None,
    'dry_run': False, 'lvm_snapsize': DEFAULT_LVM_SNAPSIZE,
    'restore_abs_path': None, 'log_file': None, 'log_level': "info",
    'mode': 'fs', 'action': 'backup', 'shadow': '', 'shadow_path': '',
    'windows_volume': '', 'command': None, 'metadata_out': None,
    'storage': 'swift', 'ssh_key': '', 'ssh_username': '', 'ssh_host': '',
    'ssh_port': DEFAULT_SSH_PORT, 'access_key': '', 'secret_key': '',
    'endpoint': '', 'compression': 'gzip', 'overwrite': False,
    'incremental': None, 'consistency_check': False,
    'consistency_checksum': None, 'nova_restore_network': None,
    'cindernative_backup_id': None, 'sync': True, 'engine_name': 'tar',
    'timeout': 120, 'project_id': None,
}

_COMMON = [
    cfg.StrOpt('action',
               choices=['backup', 'restore', 'info', 'admin', 'exec'],
               dest='action',
               help="Set the action to be taken. backup and restore are self "
                    "explanatory, info is used to retrieve info from the "
                    "storage media, exec is used to execute a script, while "
                    "admin is used to delete old backups and other admin "
                    "actions. Default backup."
               ),
    cfg.StrOpt('path-to-backup',
               short='F',
               dest='path_to_backup',
               default=DEFAULT_PARAMS['path_to_backup'],
               help='The file or directory you want to back up to Swift'
               ),
    cfg.StrOpt('backup-name',
               short='N',
               default=DEFAULT_PARAMS['backup_name'],
               help="The backup name you want to use to identify your backup "
                    "on Swift"
               ),
    cfg.StrOpt('mode',
               short='m',
               dest='mode',
               default=DEFAULT_PARAMS['mode'],
               help="Set the technology to back from. Options are, fs "
                    "(filesystem),mongo (MongoDB), mysql (MySQL), "
                    "sqlserver(SQL Server), "
                    "cinder(OpenStack Volume backup by freezer), "
                    "cindernative(OpenStack native cinder-volume backup)"
                    "nova(OpenStack Instance). Default set to fs"),
    cfg.StrOpt('engine',
               short='e',
               choices=['tar', 'rsync', 'nova', 'osbrick'],
               dest='engine_name',
               default=DEFAULT_PARAMS['engine_name'],
               help="Engine to be used for backup/restore. "
                    "With tar, the file inode will be checked for changes "
                    "amid backup execution. If the file inode changed, the "
                    "whole file will be backed up. With rsync, the data "
                    "blocks changes will be verified and only the changed "
                    "blocks will be backed up. Tar is faster, but is uses "
                    "more space and bandwidth. Rsync is slower, but uses "
                    "less space and bandwidth. Nova engine can be used to"
                    " backup/restore running instances. Backing up instances"
                    " and it's metadata.",
               required=True
               ),
    cfg.StrOpt('container',
               short='C',
               default=DEFAULT_PARAMS['container'],
               dest='container',
               help="The Swift container (or path to local storage) used to "
                    "upload files to"),
    cfg.StrOpt('snapshot',
               short='s',
               dest='snapshot',
               default=DEFAULT_PARAMS['snapshot'],
               help="Create a snapshot of the fs containing the resource to "
                    "backup. When used, the lvm parameters will be guessed "
                    "and/or the  default values will be used, on windows it "
                    "will invoke  vssadmin"),
    cfg.BoolOpt('sync',
                dest='sync',
                default=DEFAULT_PARAMS['sync'],
                help="Flush file system buffers. Force changed blocks to disk,"
                     " update the super block. Default is {0}".format(
                    DEFAULT_PARAMS['sync']
                )),
    cfg.StrOpt('lvm-srcvol',
               dest='lvm_srcvol',
               default=DEFAULT_PARAMS['lvm_srcvol'],
               help="Set the lvm volume you want to take a snapshot from. "
                    "Default no volume"),
    cfg.StrOpt('lvm-snapname',
               dest='lvm_snapname',
               default=DEFAULT_PARAMS['lvm_snapname'],
               help="Set the name of the snapshot that will be created."
                    " If not provided, a unique name will be generated."),
    cfg.StrOpt('lvm-snap-perm',
               choices=['ro', 'rw'],
               dest='lvm_snapperm',
               default=DEFAULT_PARAMS['lvm_snapperm'],
               help="Set the lvm snapshot permission to use. If the permission"
                    " is set to ro The snapshot will be immutable - read only"
                    " -. If the permission is set to rw it will be mutable"),
    cfg.StrOpt('lvm-snapsize',
               dest='lvm_snapsize',
               default=DEFAULT_PARAMS['lvm_snapsize'],
               help="Set the lvm snapshot size when creating a new "
                    "snapshot. Please add G for Gigabytes or "
                    "M for Megabytes, i.e. 500M or 8G. It is also possible "
                    "to use percentages as with the -l option of lvm, i.e. "
                    "80%%FREE Default {0}.".format(DEFAULT_LVM_SNAPSIZE)),
    cfg.StrOpt('lvm-dirmount',
               dest='lvm_dirmount',
               default=DEFAULT_PARAMS['lvm_dirmount'],
               help="Set the directory you want to mount the lvm snapshot to. "
                    "If not provided, a unique directory will be generated in "
                    "{0} ".format(DEFAULT_LVM_MOUNT_BASEDIR)),
    cfg.StrOpt('lvm-volgroup',
               dest='lvm_volgroup',
               default=DEFAULT_PARAMS['lvm_volgroup'],
               help="Specify the volume group of your logical volume. This is "
                    "important to mount your snapshot volume. Default not "
                    "set"),
    cfg.IntOpt('max-level',
               dest='max_level',
               default=DEFAULT_PARAMS['max_level'],
               help="Set the backup level used with tar to implement "
                    "incremental backup. If a level 1 is specified but "
                    "no level 0 is already available, a level 0 will be "
                    "done and subsequently backs to level 1. "
                    "Default 0 (No Incremental)"
               ),
    cfg.IntOpt('always-level',
               dest='always_level',
               default=DEFAULT_PARAMS['always_level'],
               help="Set backup maximum level used with tar to implement "
                    "incremental backup. If a level 3 is specified, the backup"
                    " will be executed from level 0 to level 3 and to that "
                    "point always a backup level 3 will be executed.  It will "
                    "not restart from level 0. This option has precedence over"
                    " --max-backup-level. Default False (Disabled)"),
    cfg.FloatOpt('restart-always-level',
                 dest='restart_always_level',
                 default=DEFAULT_PARAMS['restart_always_level'],
                 help="Restart the backup from level 0 after n days. Valid "
                      "only if --always-level option if set. If "
                      "--always-level is used together with "
                      "--remove-older-than, there might be "
                      "the chance where the initial level 0 will be removed. "
                      "Default False (Disabled)"),
    cfg.FloatOpt('remove-older-than',
                 short='R',
                 default=DEFAULT_PARAMS['remove_older_than'],
                 dest='remove_older_than',
                 help="Checks in the specified container for objects older "
                      "than the specified days. If i.e. 30 is specified, it "
                      "will remove the remote object older than 30 days. "
                      "Default False (Disabled)"),
    cfg.StrOpt('remove-from-date',
               dest='remove_from_date',
               default=DEFAULT_PARAMS['remove_from_date'],
               help="Checks the specified container and removes objects older "
                    "than the provided datetime in the form "
                    "'YYYY-MM-DDThh:mm:ss' i.e. '1974-03-25T23:23:23'. "
                    "Make sure the 'T' is between date and time "),
    cfg.StrOpt('no-incremental',
               dest='no_incremental',
               default=DEFAULT_PARAMS['no_incremental'],
               help="Disable incremental feature. By default freezer build the"
                    " meta data even for level 0 backup. By setting this "
                    "option incremental meta data is not created at all. "
                    "Default disabled"),
    cfg.StrOpt('hostname',
               dest='hostname',
               default=DEFAULT_PARAMS['hostname'],
               help="Set hostname to execute actions. If you are executing "
                    "freezer from one host but you want to delete objects "
                    "belonging to another host then you can set this option "
                    "that hostname and execute appropriate actions. Default "
                    "current node hostname."),
    cfg.StrOpt('mysql-conf',
               dest='mysql_conf',
               default=DEFAULT_PARAMS['mysql_conf'],
               help="Set the MySQL configuration file where freezer retrieve "
                    "important information as db_name, user, password, host, "
                    "port. Following is an example of config file: "
                    "# backup_mysql_conf"
                    "host     = <db-host>"
                    "user     = <mysqluser>"
                    "password = <mysqlpass>"
                    "port     = <db-port>"),
    cfg.StrOpt('metadata-out',
               dest='metadata_out',
               default=DEFAULT_PARAMS['metadata_out'],
               help="Set the filename to which write the metadata "
                    "regarding the backup metrics. Use '-' to output to "
                    "standard output."),
    cfg.StrOpt('exclude',
               dest='exclude',
               default=DEFAULT_PARAMS['exclude'],
               help="Exclude files,given as a PATTERN.Ex: --exclude '*.log' "
                    "will exclude any file with name ending with .log. "
                    "Default no exclude"
               ),
    cfg.StrOpt('dereference-symlink',
               dest='dereference_symlink',
               default=DEFAULT_PARAMS['dereference_symlink'],
               choices=[None, 'soft', 'hard', 'all'],
               help="Follow hard and soft links and archive and dump the files"
                    " they refer to. Default False."
               ),
    cfg.StrOpt('encrypt-pass-file',
               dest='encrypt_pass_file',
               default=DEFAULT_PARAMS['encrypt_pass_file'],
               help="Passing a private key to this option, allow you "
                    "to encrypt the files before to be uploaded in Swift. "
                    "Default do not encrypt."
               ),
    cfg.IntOpt('max-segment-size',
               short='M',
               default=DEFAULT_PARAMS['max_segment_size'],
               dest='max_segment_size',
               help="Set the maximum file chunk size in bytes to upload to "
                    "swift Default 33554432 bytes (32MB)"
               ),
    cfg.StrOpt('restore-abs-path',
               dest='restore_abs_path',
               default=DEFAULT_PARAMS['restore_abs_path'],
               help="Set the absolute path where you want your data restored. "
                    "Default False."
               ),
    cfg.StrOpt('restore-from-date',
               dest='restore_from_date',
               default=DEFAULT_PARAMS['restore_from_date'],
               help="Set the date of the backup from which you want to "
                    "restore.This will select the most recent backup "
                    "previous to the specified date (included). Example: "
                    "if the last backup was created at '2016-03-22T14:29:01' "
                    "and restore-from-date is set to '2016-03-22T14:29:01', "
                    "the backup will be restored successfully. The same for "
                    "any date after that, even if the provided date is in the "
                    "future. However if restore-from-date is set to "
                    "'2016-03-22T14:29:00' or before, that backup will not "
                    "be found. "
                    "Please provide datetime in format 'YYYY-MM-DDThh:mm:ss' "
                    "i.e. '1979-10-03T23:23:23'. Make sure the 'T' is between "
                    "date and time Default None."
               ),
    cfg.StrOpt('max-priority',
               dest='max_priority',
               default=DEFAULT_PARAMS['max_priority'],
               help="Set the cpu process to the highest priority (i.e. -20 on "
                    "Linux) and real-time for I/O. The process priority "
                    "will be set only if nice and ionice are installed "
                    "Default disabled. Use with caution."
               ),
    cfg.BoolOpt('quiet',
                short='q',
                default=DEFAULT_PARAMS['quiet'],
                dest='quiet',
                help="Suppress error messages"
                ),
    cfg.BoolOpt('insecure',
                dest='insecure',
                default=DEFAULT_PARAMS['insecure'],
                help='Allow to access swift servers without checking SSL '
                     'certs.'),
    cfg.StrOpt('os-identity-api-version',
               deprecated_name='os-auth-ver',
               default=DEFAULT_PARAMS['os_identity_api_version'],
               dest='os_identity_api_version',
               choices=['1', '2', '2.0', '3'],
               help="Openstack identity api version, can be 1, 2, 2.0 or 3"
               ),
    cfg.StrOpt('proxy',
               dest='proxy',
               default=DEFAULT_PARAMS['proxy'],
               help="Enforce proxy that alters system HTTP_PROXY and "
                    "HTTPS_PROXY, use \'\' to eliminate all system proxies"
               ),
    cfg.BoolOpt('dry-run',
                dest='dry_run',
                default=DEFAULT_PARAMS['dry_run'],
                help="Do everything except writing or removing objects"
                ),
    cfg.IntOpt('upload-limit',
               dest='upload_limit',
               default=DEFAULT_PARAMS['upload_limit'],
               help="Upload bandwidth limit in Bytes per sec. "
                    "Can be invoked with dimensions (10K, 120M, 10G)."),
    cfg.IntOpt('download-limit',
               dest='download_limit',
               default=DEFAULT_PARAMS['download_limit'],
               help="Download bandwidth limit in Bytes per sec. Can be "
                    "invoked  with dimensions (10K, 120M, 10G)."),
    cfg.StrOpt('cinder-vol-id',
               dest='cinder_vol_id',
               default=DEFAULT_PARAMS['cinder_vol_id'],
               help="Id of cinder volume for backup"
               ),
    cfg.StrOpt('cinderbrick-vol-id',
               dest='cinderbrick_vol_id',
               default=DEFAULT_PARAMS['cinderbrick_vol_id'],
               help="Id of cinder volume for backup using os-brick"
               ),
    cfg.StrOpt('cindernative-vol-id',
               dest='cindernative_vol_id',
               default=DEFAULT_PARAMS['cindernative_vol_id'],
               help="Id of cinder volume for native backup"
               ),
    cfg.StrOpt('cindernative-backup-id',
               default=DEFAULT_PARAMS['cindernative_backup_id'],
               dest='cindernative_backup_id',
               help="Id of the cindernative backup to be restored"
               ),
    cfg.StrOpt('nova-inst-id',
               dest='nova_inst_id',
               default=DEFAULT_PARAMS['nova_inst_id'],
               help="Id of nova instance for backup"
               ),
    cfg.StrOpt('project-id',
               dest='project_id',
               default=DEFAULT_PARAMS['project_id'],
               help="Id of project for backup"
               ),
    cfg.StrOpt('sql-server-conf',
               dest='sql_server_conf',
               default=DEFAULT_PARAMS['sql_server_conf'],
               help="Set the SQL Server configuration file where freezer "
                    "retrieve the sql server instance. Following is an example"
                    " of config file: instance = <db-instance>"
               ),
    cfg.StrOpt('command',
               dest='command',
               default=DEFAULT_PARAMS['command'],
               help="Command executed by exec action"
               ),
    cfg.StrOpt('compression',
               dest='compression',
               default=DEFAULT_PARAMS['compression'],
               choices=['gzip', 'bzip2', 'xz'],
               help="Compression algorithm to use. Gzip is default algorithm"
               ),
    cfg.StrOpt('storage',
               dest='storage',
               default=DEFAULT_PARAMS['storage'],
               choices=['local', 'swift', 'ssh', 's3'],
               help="Storage for backups. Can be Swift, Local, SSH and S3 "
                    "now. Swift is default storage now. Local stores backups"
                    "on the same defined path, swift will store files in "
                    "container, and s3 will store files in bucket in S3 "
                    "compatible storage."
               ),
    cfg.StrOpt('access-key',
               dest='access_key',
               default=DEFAULT_PARAMS['access_key'],
               help="Access key for S3 compatible storage"
               ),
    cfg.StrOpt('secret-key',
               dest='secret_key',
               default=DEFAULT_PARAMS['secret_key'],
               help="Secret key for S3 compatible storage"
               ),
    cfg.StrOpt('endpoint',
               dest='endpoint',
               default=DEFAULT_PARAMS['endpoint'],
               help="Endpoint of S3 compatible storage"
               ),
    cfg.StrOpt('ssh-key',
               dest='ssh_key',
               default=DEFAULT_PARAMS['ssh_key'],
               help="Path to ssh-key for ssh storage only"
               ),
    cfg.StrOpt('ssh-username',
               dest='ssh_username',
               default=DEFAULT_PARAMS['ssh_username'],
               help="Remote username for ssh storage only"
               ),
    cfg.StrOpt('ssh-host',
               dest='ssh_host',
               default=DEFAULT_PARAMS['ssh_host'],
               help="Remote host for ssh storage only"
               ),
    cfg.IntOpt('ssh-port',
               dest='ssh_port',
               default=DEFAULT_PARAMS['ssh_port'],
               help="Remote port for ssh storage only (default 22)"
               ),
    cfg.StrOpt('config',
               dest='config',
               default=DEFAULT_PARAMS['config'],
               help="Config file abs path. Option arguments are provided from "
                    "config file. When config file is used any option from "
                    "command line provided take precedence."),
    cfg.BoolOpt('overwrite',
                dest='overwrite',
                default=DEFAULT_PARAMS['overwrite'],
                help='With overwrite removes files from restore path before '
                     'restore.'),
    cfg.BoolOpt('consistency-check',
                dest='consistency_check',
                default=DEFAULT_PARAMS['consistency_check'],
                help="Compute the checksum of the fileset before backup. "
                     "This checksum is stored as part of the backup metadata, "
                     "which can be obtained either by using --metadata-out or "
                     "through the freezer API. "
                     "On restore, it is possible to verify for consistency. "
                     "Please note this option is currently only available "
                     "for file system backups. "
                     "Please also note checking backup consistency is a "
                     "resource intensive operation, so use it carefully!"),
    cfg.StrOpt('consistency-checksum',
               dest='consistency_checksum',
               default=DEFAULT_PARAMS['consistency_checksum'],
               help="Compute the checksum of the restored file(s) and compare "
                    "it to the (provided) checksum to verify that the backup "
                    "was successful"),
    cfg.BoolOpt('incremental',
                default=DEFAULT_PARAMS['incremental'],
                help="When the option is set, freezer will perform a "
                     "cindernative incremental backup instead of the default "
                     "full backup. And if True, but volume do not have a base"
                     "full backup, freezer will do a full backup first"),
    cfg.StrOpt('nova-restore-network',
               dest='nova_restore_network',
               default=DEFAULT_PARAMS['nova_restore_network'],
               help="ID of the network to attach to the restored VM. "
                    "In the case of a project containing multiple networks, "
                    "it is necessary to provide the ID of the network to "
                    "attach to the restored VM."),
    cfg.IntOpt('timeout',
               dest='timeout',
               default=DEFAULT_PARAMS['timeout'],
               help="Timeout for the running operation. This option can be "
                    "used with any operation running with freezer and after "
                    "this time it will raise a TimeOut Exception. Default is"
                    " {0}".format(DEFAULT_PARAMS['timeout'])
               ),
]


def config(args=[]):
    CONF.register_opts(_COMMON)
    CONF.register_cli_opts(_COMMON)
    default_conf = None
    log.register_options(CONF)
    CONF(args=args,
         project='freezer',
         default_config_files=default_conf,
         version=FREEZER_VERSION)


def setup_logging():
    """Set some oslo log defaults."""
    # disable freezer from logging to stderr
    CONF.set_default('use_stderr', False)
    CONF.set_default('log_file', prepare_logging())
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    log.setup(CONF, 'freezer', version=FREEZER_VERSION)


def get_backup_args():

    defaults = DEFAULT_PARAMS.copy()

    class FreezerConfig(object):
        def __init__(self, args):
            self.__dict__.update(args)

    cli_options = dict([(x, y) for x, y in CONF.iteritems() if y is not None])

    defaults.update(cli_options)

    conf = None
    if CONF.get('config'):
        conf = freezer_config.Config.parse(CONF.get('config'))

        # force log_config_append to always exists in defaults even if not
        # provided.
        defaults['log_config_append'] = None

        defaults.update(conf.default)
        for config_key in conf.default.keys():
            try:
                CONF.set_override(config_key, conf.default[config_key])
            except NoSuchOptError:
                LOG.debug('No such opt, {0}, so set it'.format(config_key))
                setattr(CONF, config_key, conf.default[config_key])
            except KeyError:
                real_opt, real_group = CONF._find_deprecated_opts(config_key)
                if '-' in real_opt:
                    real_opt = real_opt.replace('-', '_')
                CONF.set_override(real_opt, conf.default[real_opt])

        if defaults['log_file']:
            CONF.set_override('log_file', defaults['log_file'])

        CONF.set_override('default_log_levels', _DEFAULT_LOG_LEVELS)

    if not CONF.get('log_file'):
        log_file = None
        for file_name in ['/var/log/freezer-agent/freezer-agent.log',
                          '/var/log/freezer.log']:
            try:
                log_file = prepare_logging(file_name)
            except IOError:
                pass

        if not log_file:
            # Set default working directory to ~/.freezer. If the directory
            # does not exists it is created
            work_dir = os.path.join(home, '.freezer')
            if not os.path.exists(work_dir):
                try:
                    os.makedirs(work_dir)
                    log_file = prepare_logging(os.path.join(work_dir,
                                                            'freezer.log'))
                except (OSError, IOError) as err_msg:
                    # This avoids freezer-agent to crash if it can't write to
                    # ~/.freezer, which may happen on some env (for me,
                    # it happens in Jenkins, as freezer-agent can't write to
                    # /var/lib/jenkins).
                    print(encodeutils.safe_decode('{}'.format(err_msg)),
                          file=sys.stderr)
        if log_file:
            CONF.set_default('log_file', log_file)
        else:
            LOG.warning("log file cannot be created. Freezer will proceed with"
                        " default stdout and stderr")

    backup_args = FreezerConfig(defaults)

    if CONF.get('config'):
        backup_args.__dict__['config'] = CONF.get('config')

    # Set default working directory to ~/.freezer. If the directory
    # does not exists it is created
    work_dir = os.path.join(home, '.freezer')
    backup_args.__dict__['work_dir'] = work_dir
    if not os.path.exists(work_dir):
        try:
            os.makedirs(work_dir)
        except (OSError, IOError) as err_msg:
            # This avoids freezer-agent to crash if it can't write to
            # ~/.freezer, which may happen on some env (for me,
            # it happens in Jenkins, as freezer-agent can't write to
            # /var/lib/jenkins).
            print(encodeutils.safe_decode('{}'.format(err_msg)),
                  file=sys.stderr)

    # If hostname is not set, hostname of the current node will be used
    if not backup_args.hostname:
        backup_args.__dict__['hostname'] = socket.gethostname()

    # If we have provided --proxy then overwrite the system HTTP_PROXY and
    # HTTPS_PROXY
    if backup_args.proxy:
        utils.alter_proxy(backup_args.proxy)

    # MySQLdb object
    backup_args.__dict__['mysql_db_inst'] = ''
    backup_args.__dict__['storages'] = None
    if conf and conf.storages:
        backup_args.__dict__['storages'] = conf.storages

    # Windows volume
    backup_args.__dict__['shadow'] = ''
    backup_args.__dict__['shadow_path'] = ''
    backup_args.__dict__['file_name'] = ''
    if winutils.is_windows():
        if backup_args.path_to_backup:
            backup_args.__dict__['windows_volume'] = \
                backup_args.path_to_backup[:3]

    backup_media = 'fs'
    if backup_args.cinder_vol_id:
        backup_media = 'cinder'
    elif backup_args.cindernative_vol_id or backup_args.cindernative_backup_id:
        backup_media = 'cindernative'
    elif backup_args.engine_name == 'nova' and (backup_args.project_id or
                                                backup_args.nova_inst_id):
        backup_media = 'nova'
    elif backup_args.cinderbrick_vol_id:
        backup_media = 'cinderbrick'

    backup_args.__dict__['backup_media'] = backup_media

    backup_args.__dict__['time_stamp'] = None

    if backup_args.upload_limit != -1 or backup_args.download_limit != -1 and \
            not winutils.is_windows():
        # handle --config option with tmp config file
        if backup_args.config:
            conf_file = tempfile.NamedTemporaryFile(prefix='freezer_job_',
                                                    delete=False)
            # remove the limits from the new file
            if 'upload_limit' in conf.default:
                conf.default.pop('upload_limit')
            elif 'download_limit' in conf.default:
                conf.default.pop('download_limit')

            utils.save_config_to_file(conf.default, conf_file,
                                      'default')
            # replace the original file with the tmp one
            conf_index = sys.argv.index('--config') + 1
            sys.argv[conf_index] = conf_file.name

        # if limits provided from cli remove it !
        if '--upload-limit' in sys.argv:
            index = sys.argv.index('--upload-limit')
            sys.argv.pop(index)
            sys.argv.pop(index)
        if '--download-limit' in sys.argv:
            index = sys.argv.index('--download-limit')
            sys.argv.pop(index)
            sys.argv.pop(index)
        # locate trickle
        trickle_executable = distspawn.find_executable('trickle')
        if trickle_executable is None:
            trickle_executable = distspawn.find_executable(
                'trickle', path=":".join(sys.path))
            if trickle_executable is None:
                        trickle_executable = distspawn.find_executable(
                            'trickle', path=":".join(os.environ.get('PATH')))

        if trickle_executable:
            LOG.info("Info: Starting trickle ...")
            trickle_command = '{0} -d {1} -u {2} '.\
                format(trickle_executable,
                       getattr(backup_args, 'download_limit') or -1,
                       getattr(backup_args, 'upload_limit') or -1)
            backup_args.__dict__['trickle_command'] = trickle_command
            if backup_args.config:
                backup_args.__dict__['tmp_file'] = conf_file.name

            # maintain env variable not to get into infinite loop
            if "tricklecount" in os.environ:
                tricklecount = int(os.environ.get("tricklecount", 1))
                tricklecount += 1
                os.environ["tricklecount"] = str(tricklecount)

            else:
                os.environ["tricklecount"] = str(1)
        else:
            LOG.warning("Trickle not found. Switching to normal mode without "
                        "limiting bandwidth")
            if backup_args.config:
                # remove index tmp_file from backup arguments dict
                utils.delete_file(conf_file.name)

    return backup_args


def prepare_logging(log_file=None):
    """
    Creates log directory and log file if no log files provided
    :return:
    """
    if not log_file:
        log_file = os.path.join(home, '.freezer', 'freezer.log')
    expanded_file_name = os.path.expanduser(log_file)
    expanded_dir_name = os.path.dirname(expanded_file_name)
    utils.create_dir(expanded_dir_name, do_log=False)
    return expanded_file_name


def list_opts():
    _OPTS = {
        None: _COMMON
    }

    return _OPTS.items()
