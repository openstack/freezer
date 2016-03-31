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
from oslo_config import cfg
from oslo_log import log
from oslo_utils import encodeutils
import socket
import sys
from tempfile import NamedTemporaryFile

from freezer import __version__ as FREEZER_VERSION
from freezer.utils import config as freezer_config
from freezer.utils import utils
from freezer.utils import winutils


CONF = cfg.CONF
LOG = log.getLogger(__name__)

home = os.path.expanduser("~")

DEFAULT_LVM_SNAPSIZE = '1G'
DEFAULT_LVM_MOUNT_BASENAME = '/var/lib/freezer'
DEFAULT_LVM_SNAP_BASENAME = 'freezer_backup_snap'
DEFAULT_SSH_PORT = 22

DEFAULT_PARAMS = {
    'os_identity_api_version': None,
    'lvm_auto_snap': None, 'lvm_volgroup': False,
    'exclude': False, 'sql_server_conf': False,
    'backup_name': False, 'quiet': False,
    'container': 'freezer_backups', 'no_incremental': False,
    'max_segment_size': 33554432, 'lvm_srcvol': False,
    'download_limit': -1, 'hostname': False, 'remove_from_date': False,
    'restart_always_level': False, 'lvm_dirmount': None,
    'dereference_symlink': '',
    'config': False, 'mysql_conf': False,
    'insecure': False, 'lvm_snapname': None,
    'lvm_snapperm': 'ro', 'snapshot': False,
    'max_priority': False, 'max_level': False, 'path_to_backup': False,
    'encrypt_pass_file': False, 'volume': False, 'proxy': False,
    'cinder_vol_id': '', 'cindernative_vol_id': '',
    'nova_inst_id': '', '__version__': FREEZER_VERSION,
    'remove_older_than': None, 'restore_from_date': False,
    'upload_limit': -1, 'always_level': False, 'version': False,
    'dry_run': False, 'lvm_snapsize': DEFAULT_LVM_SNAPSIZE,
    'restore_abs_path': False, 'log_file': None, 'log_level': "info",
    'mode': 'fs', 'action': 'backup', 'shadow': '', 'shadow_path': '',
    'windows_volume': '', 'command': None, 'metadata_out': False,
    'storage': 'swift', 'ssh_key': '', 'ssh_username': '', 'ssh_host': '',
    'ssh_port': DEFAULT_SSH_PORT, 'compression': 'gzip',
    'overwrite': False,
    'consistency_check': False, 'consistency_checksum': None,
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
               default=False,
               help='The file or directory you want to back up to Swift'
               ),
    cfg.StrOpt('backup-name',
               short='N',
               default=False,
               help="The backup name you want to use to identify your backup "
                    "on Swift"
               ),
    cfg.StrOpt('mode',
               short='m',
               dest='mode',
               help="Set the technology to back from. Options are, fs "
                    "(filesystem),mongo (MongoDB), mysql (MySQL), sqlserver "
                    "(SQL Server) Default set to fs"),
    cfg.StrOpt('container',
               short='C',
               default='freezer_backups',
               dest='container',
               help="The Swift container (or path to local storage) used to "
                    "upload files to"),
    cfg.StrOpt('snapshot',
               short='s',
               dest='snapshot',
               help="Create a snapshot of the fs containing the resource to "
                    "backup. When used, the lvm parameters will be guessed "
                    "and/or the  default values will be used, on windows it "
                    "will invoke  vssadmin"),
    cfg.StrOpt('lvm-auto-snap',
               dest='lvm_auto_snap',
               help="(Deprecated) Please use --snapshot instead"
                    "Automatically guess the volume group and volume name for "
                    "given PATH."),
    cfg.StrOpt('lvm-srcvol',
               dest='lvm_srcvol',
               help="Set the lvm volume you want to take a snaphost from. "
                    "Default no volume"),
    cfg.StrOpt('lvm-snapname',
               dest='lvm_snapname',
               help="Set the name of the snapshot that will be created."
                    " If not provided, a unique name will be generated."),
    cfg.StrOpt('lvm-snap-perm',
               choices=['ro', 'rw'],
               dest='lvm_snapperm',
               help="Set the lvm snapshot permission to use. If the permission"
                    " is set to ro The snapshot will be immutable - read only"
                    " -. If the permission is set to rw it will be mutable"),
    cfg.StrOpt('lvm-snapsize',
               dest='lvm_snapsize',
               help="Set the lvm snapshot size when creating a new snapshot. "
                    "Please add G for Gigabytes or M for Megabytes, i.e. 500M "
                    "or 8G. It is also possible to use percentages as with the"
                    " -l option of lvm, i.e. 80%%FREE Default {0}.".format(
                    DEFAULT_LVM_SNAPSIZE)),
    cfg.StrOpt('lvm-dirmount',
               dest='lvm_dirmount',
               help="Set the directory you want to mount the lvm snapshot to. "
                    "If not provided, a unique name will be generated with the"
                    "basename {0} ".format(DEFAULT_LVM_MOUNT_BASENAME)),
    cfg.StrOpt('lvm-volgroup',
               dest='lvm_volgroup',
               help="Specify the volume group of your logical volume. This is "
                    "important to mount your snapshot volume. Default not set"),
    cfg.IntOpt('max-level',
               dest='max_level',
               help="Set the backup level used with tar to implement "
                    "incremental backup. If a level 1 is specified but no level"
                    " 0 is already available, a level 0 will be done and "
                    "subsequently backs to level 1. Default 0 (No Incremental)"
               ),
    cfg.IntOpt('always-level',
               dest='always_level',
               help="Set backup maximum level used with tar to implement "
                    "incremental backup. If a level 3 is specified, the backup"
                    " will be executed from level 0 to level 3 and to that "
                    "point always a backup level 3 will be executed.  It will "
                    "not restart from level 0. This option has precedence over"
                    " --max-backup-level. Default False (Disabled)"),
    cfg.FloatOpt('restart-always-level',
                 dest='restart_always_level',
                 help="Restart the backup from level 0 after n days. Valid only"
                      " if --always-level option if set. If --always-level is "
                      "used together with --remove-older-then, there might be "
                      "the chance where the initial level 0 will be removed. "
                      "Default False (Disabled)"),
    cfg.FloatOpt('remove-older-than',
                 short='R',
                 dest='remove_older_than',
                 help="Checks in the specified container for object older than "
                      "the specified days. If i.e. 30 is specified, it will "
                      "remove the remote object older than 30 days. Default "
                      "False (Disabled) The option --remove-older-then is "
                      "deprecated and will be removed soon",
                 deprecated_for_removal=True),
    cfg.StrOpt('remove-from-date',
               dest='remove_from_date',
               help="Checks the specified container and removes objects older "
                    "than the provided datetime in the form "
                    "'YYYY-MM-DDThh:mm:ss' i.e. '1974-03-25T23:23:23'. "
                    "Make sure the 'T' is between date and time "),
    cfg.StrOpt('no-incremental',
               dest='no_incremental',
               help="Disable incremental feature. By default freezer build the"
                    " meta data even for level 0 backup. By setting this option"
                    " incremental meta data is not created at all. Default "
                    "disabled"),
    cfg.StrOpt('hostname',
               dest='hostname',
               deprecated_name='restore-from-host',
               help="Set hostname to execute actions. If you are executing "
                    "freezer from one host but you want to delete objects "
                    "belonging to another host then you can set this option "
                    "that hostname and execute appropriate actions. Default "
                    "current node hostname."),
    cfg.StrOpt('mysql-conf',
               dest='mysql_conf',
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
               help="Set the filename to which write the metadata regarding the"
                    " backup metrics. Use '-' to output to standard output."),
    cfg.StrOpt('exclude',
               dest='exclude',
               help="Exclude files,given as a PATTERN.Ex: --exclude '*.log' "
                    "will exclude any file with name ending with .log. "
                    "Default no exclude"
               ),
    cfg.StrOpt('dereference-symlink',
               dest='dereference_symlink',
               choices=['none', 'soft', 'hard', 'all'],
               help="Follow hard and soft links and archive and dump the files"
                    " they refer to. Default False."
               ),
    cfg.StrOpt('encrypt-pass-file',
               dest='encrypt_pass_file',
               help="Passing a private key to this option, allow you to encrypt"
                    " the files before to be uploaded in Swift. Default do "
                    "not encrypt."
               ),
    cfg.IntOpt('max-segment-size',
               short='M',
               dest='max_segment_size',
               help="Set the maximum file chunk size in bytes to upload to "
                    "swift Default 33554432 bytes (32MB)"
               ),
    cfg.StrOpt('restore-abs-path',
               dest='restore_abs_path',
               help="Set the absolute path where you want your data restored. "
                    "Default False."
               ),
    cfg.StrOpt('restore-from-date',
               dest='restore_from_date',
               help="Set the date of the backup from which you want to restore."
                    "This will select the most recent backup previous to "
                    "the specified date (included). Example: "
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
               help="Set the cpu process to the highest priority (i.e. -20 on "
                    "Linux) and real-time for I/O. The process priority will be"
                    " set only if nice and ionice are installed Default "
                    "disabled. Use with caution."
               ),
    cfg.BoolOpt('quiet',
                short='q',
                dest='quiet',
                help="Suppress error messages"
                ),
    cfg.BoolOpt('insecure',
                dest='insecure',
                help='Allow to access swift servers without checking SSL '
                     'certs.'),
    cfg.StrOpt('os-identity-api-version',
               deprecated_name='os-auth-ver',
               dest='os_identity_api_version',
               choices=['1', '2', '2.0', '3'],
               help="Openstack identity api version, can be 1, 2, 2.0 or 3"
               ),
    cfg.StrOpt('proxy',
               dest='proxy',
               help="Enforce proxy that alters system HTTP_PROXY and "
                    "HTTPS_PROXY, use \'\' to eliminate all system proxies"
               ),
    cfg.BoolOpt('dry-run',
                dest='dry_run',
                help="Do everything except writing or removing objects"
                ),
    cfg.IntOpt('upload-limit',
               dest='upload_limit',
               help="Upload bandwidth limit in Bytes per sec. "
                    "Can be invoked with dimensions (10K, 120M, 10G)."),
    cfg.IntOpt('download-limit',
               dest='download_limit',
               help="Download bandwidth limit in Bytes per sec. Can be invoked "
                    " with dimensions (10K, 120M, 10G)."),
    cfg.StrOpt('cinder-vol-id',
               dest='cinder_vol_id',
               help="Id of cinder volume for backup"
               ),
    cfg.StrOpt('cindernative-vol-id',
               dest='cindernative_vol_id',
               help="Id of cinder volume for native backup"
               ),
    cfg.StrOpt('nova-inst-id',
               dest='nova_inst_id',
               help="Id of nova instance for backup"
               ),
    cfg.StrOpt('sql-server-conf',
               dest='sql_server_conf',
               help="Set the SQL Server configuration file where freezer "
                    "retrieve the sql server instance. Following is an example"
                    " of config file: instance = <db-instance>"
               ),
    cfg.StrOpt('command',
               dest='command',
               help="Command executed by exec action"
               ),
    cfg.StrOpt('compression',
               dest='compression',
               choices=['gzip', 'bzip2', 'xz'],
               help="compression algorithm to use. gzip is default algorithm"
               ),
    cfg.StrOpt('storage',
               dest='storage',
               choices=['local', 'swift', 'ssh'],
               help="Storage for backups. Can be Swift or Local now. Swift is "
                    "default storage now. Local stores backups on the same "
                    "defined path and swift will store files in container."
               ),
    cfg.StrOpt('ssh-key',
               dest='ssh_key',
               help="Path to ssh-key for ssh storage only"
               ),
    cfg.StrOpt('ssh-username',
               dest='ssh_username',
               help="Remote username for ssh storage only"
               ),
    cfg.StrOpt('ssh-host',
               dest='ssh_host',
               help="Remote host for ssh storage only"
               ),
    cfg.IntOpt('ssh-port',
               dest='ssh_port',
               help="Remote port for ssh storage only (default 22)"
               ),
    cfg.StrOpt('config',
               dest='config',
               help="Config file abs path. Option arguments are provided from "
                    "config file. When config file is used any option from "
                    "command line provided take precedence."),
    cfg.BoolOpt('overwrite',
                dest='overwrite',
                help='With overwrite removes files from restore path before '
                     'restore.'),
    cfg.BoolOpt('consistency_check',
                dest='consistency_check',
                help="When true will checksum the files before backup. "
                     "The commuted backup checksum is stored as bakcup metadata"
                     " and can be retrieved through the freezer-api. "
                     "On restore it is possible to check for consistency. "
                     "Please note this option is currently only available "
                     "for file system backups. "
                     "Please also note backup consistency is a resource "
                     "consuming operation so use it carefully."),
    cfg.StrOpt('consistency_checksum',
               dest='consistency_checksum',
               help="Checksum the restored file(s) and compares to the "
                    "backup consistency_checksum provided. "
                    "Allows verification that the restored file(s) matches "
                    "the original file(s) before backup. "),
]


def config():
    CONF.register_opts(_COMMON)
    CONF.register_cli_opts(_COMMON)
    default_conf = None
    log.register_options(CONF)
    CONF(args=sys.argv[1:],
         project='freezer',
         default_config_files=default_conf,
         version=FREEZER_VERSION)


def setup_logging():
    """Set some oslo log defaults."""
    _DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                           'qpid=WARN', 'stevedore=WARN', 'oslo_log=INFO',
                           'iso8601=WARN',
                           'requests.packages.urllib3.connectionpool=WARN',
                           'urllib3.connectionpool=WARN', 'websocket=WARN',
                           'keystonemiddleware=WARN', 'freezer=INFO']

    _DEFAULT_LOGGING_CONTEXT_FORMAT = (
        '%(asctime)s.%(msecs)03d %(process)d '
        '%(levelname)s %(name)s [%(request_id)s '
        '%(user_identity)s] %(instance)s'
        '%(message)s')
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
        defaults.update(conf.default)
        # TODO: restore_from_host is deprecated and to be removed
        defaults['hostname'] = conf.default.get('hostname') or \
                               conf.default.get('restore_from_host')

        # override default oslo values
        levels = {
            'all': log.NOTSET,
            'debug': log.DEBUG,
            'warn': log.WARN,
            'info': log.INFO,
            'error': log.ERROR,
            'critical': log.CRITICAL
        }
        if not CONF.get('log_file'):
            CONF.set_override('log_file', levels.get(defaults['log_file'],
                                                     log.NOTSET))
        CONF.set_override('default_log_levels', defaults['log_level'])
    if not CONF.get('log_file'):
        log_file = None
        for file_name in ['/var/log/freezer.log', '~/.freezer/freezer.log']:
            try:
                log_file = prepare_logging(file_name)
            except IOError:
                pass
        if log_file:
            CONF.set_default('log_file', log_file)
        else:
            LOG.warn("log file cannot be created. Freezer will proceed with "
                     "default stdout and stderr")

    backup_args = FreezerConfig(defaults)
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

    # todo(enugaev) move it to new command line param backup_media

    if backup_args.lvm_auto_snap:
        raise Exception('lvm-auto-snap is deprecated. '
                        'Please use --snapshot instead')
    backup_media = 'fs'
    if backup_args.cinder_vol_id:
        backup_media = 'cinder'
    elif backup_args.cindernative_vol_id:
        backup_media = 'cindernative'
    elif backup_args.nova_inst_id:
        backup_media = 'nova'

    backup_args.__dict__['backup_media'] = backup_media

    backup_args.__dict__['time_stamp'] = None

    if backup_args.upload_limit != -1 or backup_args.download_limit != -1 and \
            not winutils.is_windows():
        # handle --config option with tmp config file
        if backup_args.config:
            conf_file = NamedTemporaryFile(prefix='freezer_job_', delete=False)
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
            LOG.info("[*] Info: Starting trickle ...")
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
            LOG.warn("[*] Trickle not found. Switching to normal mode without "
                     "limiting bandwidth")
            if backup_args.config:
                # remove index tmp_file from backup arguments dict
                backup_args.__dict__.pop('tmp_file')
                utils.delete_file(conf_file.name)

    return backup_args


def prepare_logging(log_file='~/.freezer/freezer.log'):
    """
    Creates log directory and log file if no log files provided
    :return:
    """
    expanded_file_name = os.path.expanduser(log_file)
    expanded_dir_name = os.path.dirname(expanded_file_name)
    utils.create_dir(expanded_dir_name, do_log=False)
    return expanded_file_name


def list_opts():
    _OPTS = {
        None: _COMMON
    }

    return _OPTS.items()
