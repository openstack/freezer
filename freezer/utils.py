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

Freezer general utils functions
"""

import logging
import os
import time
import datetime
import re
import subprocess


class OpenstackOptions:
    """
    Stores credentials for OpenStack API.
    Can be created using
    >> create_from_env()
    or
    >> create_from_dict(dict)
    """
    def __init__(self, user_name, tenant_name, auth_url, password,
                 tenant_id=None, region_name=None):
        self.user_name = user_name
        self.tenant_name = tenant_name
        self.auth_url = auth_url
        self.password = password
        self.tenant_id = tenant_id
        self.region_name = region_name

    @property
    def os_options(self):
        """
        :return: The OpenStack options which can have tenant_id,
                 auth_token, service_type, endpoint_type, tenant_name,
                 object_storage_url, region_name
        """
        return {'tenant_id': self.tenant_id,
                'tenant_name': self.tenant_name,
                'region_name': self.region_name}

    @staticmethod
    def create_from_env():
        return OpenstackOptions.create_from_dict(os.environ)

    @staticmethod
    def create_from_dict(src_dict):
        try:
            return OpenstackOptions(
                user_name=src_dict['OS_USERNAME'],
                tenant_name=src_dict['OS_TENANT_NAME'],
                auth_url=src_dict['OS_AUTH_URL'],
                password=src_dict['OS_PASSWORD'],
                tenant_id=src_dict.get('OS_TENANT_ID', None),
                region_name=src_dict.get('OS_REGION_NAME', None)
            )
        except Exception as e:
            raise Exception('Missing Openstack connection parameter: {0}'
                            .format(e))


def gen_manifest_meta(
        backup_opt_dict, manifest_meta_dict, meta_data_backup_file):
    ''' This function is used to load backup metadata information on Swift.
     this is used to keep information between consecutive backup
     executions.
     If the manifest_meta_dict is available, most probably this is not
     the first backup run for the provided backup name and host.
     In this case we remove all the conflictive keys -> values from
     the dictionary.
     '''

    if manifest_meta_dict.get('x-object-meta-tar-prev-meta-obj-name'):
        tar_meta_prev = \
            manifest_meta_dict['x-object-meta-tar-prev-meta-obj-name']
        tar_meta_to_upload = \
            manifest_meta_dict['x-object-meta-tar-meta-obj-name'] = \
            manifest_meta_dict['x-object-meta-tar-prev-meta-obj-name'] = \
            meta_data_backup_file
    else:
        manifest_meta_dict['x-object-meta-tar-prev-meta-obj-name'] = \
            meta_data_backup_file
        manifest_meta_dict['x-object-meta-backup-name'] = \
            backup_opt_dict.backup_name
        manifest_meta_dict['x-object-meta-src-file-to-backup'] = \
            backup_opt_dict.path_to_backup
        manifest_meta_dict['x-object-meta-abs-file-path'] = ''

        # Set manifest meta if encrypt_pass_file is provided
        # The file will contain a plain password that will be used
        # to encrypt and decrypt tasks
        manifest_meta_dict['x-object-meta-encrypt-data'] = 'Yes'
        if backup_opt_dict.encrypt_pass_file is False:
            manifest_meta_dict['x-object-meta-encrypt-data'] = ''
        manifest_meta_dict['x-object-meta-always-backup-level'] = ''
        if backup_opt_dict.always_level:
            manifest_meta_dict['x-object-meta-always-backup-level'] = \
                backup_opt_dict.always_level

        # Set manifest meta if max_level argument is provided
        # Once the incremental backup arrive to max_level, it will
        # restart from level 0
        manifest_meta_dict['x-object-meta-maximum-backup-level'] = ''
        if backup_opt_dict.max_level is not False:
            manifest_meta_dict['x-object-meta-maximum-backup-level'] = \
                str(backup_opt_dict.max_level)

        # At the end of the execution, checks the objects ages for the
        # specified swift container. If there are object older then the
        # specified days they'll be removed.
        # Unit is int and every int and 5 == five days.
        manifest_meta_dict['x-object-meta-remove-backup-older-than-days'] = ''
        if backup_opt_dict.remove_older_than is not False:
            manifest_meta_dict['x-object-meta-remove-backup-older-than-days'] \
                = '{0}'.format(backup_opt_dict.remove_older_than)
        manifest_meta_dict['x-object-meta-hostname'] = backup_opt_dict.hostname
        manifest_meta_dict['x-object-meta-segments-size-bytes'] = \
            str(backup_opt_dict.max_segment_size)
        manifest_meta_dict['x-object-meta-backup-created-timestamp'] = \
            str(backup_opt_dict.time_stamp)
        manifest_meta_dict['x-object-meta-providers-list'] = 'HP'
        manifest_meta_dict['x-object-meta-tar-meta-obj-name'] = \
            meta_data_backup_file
        tar_meta_to_upload = tar_meta_prev = \
            manifest_meta_dict['x-object-meta-tar-meta-obj-name'] = \
            manifest_meta_dict['x-object-meta-tar-prev-meta-obj-name']

        # Need to be processed from the last existing backup file found
        # in Swift, matching with hostname and backup name
        # the last existing file can be extracted from the timestamp
        manifest_meta_dict['x-object-meta-container-segments'] = \
            backup_opt_dict.container_segments

        # Set the restart_always_level value to n days. According
        # to the following option, when the always_level is set
        # the backup will be reset to level 0 if the current backup
        # times tamp is older then the days in x-object-meta-container-segments
        manifest_meta_dict['x-object-meta-restart-always-backup'] = ''
        if backup_opt_dict.restart_always_level is not False:
            manifest_meta_dict['x-object-meta-restart-always-backup'] = \
                backup_opt_dict.restart_always_level

    return (
        backup_opt_dict, manifest_meta_dict,
        tar_meta_to_upload, tar_meta_prev)


def validate_all_args(required_list):
    '''
    Ensure ALL the elements of required_list are True. raise ValueError
    Exception otherwise
    '''

    try:
        for element in required_list:
            if not element:
                return False
    except Exception as error:
        raise Exception('validate_all_args: {0} {1}'
                        .format(required_list, error))

    return True


def sort_backup_list(backup_opt_dict):
    """
    Sort the backups by timestamp. The provided list contains strings in the
    format hostname_backupname_timestamp_level
    """

    # Remove duplicates objects
    backups_list = list(set(backup_opt_dict.remote_match_backup))

    backups_list.sort(
        key=lambda x: map(lambda y: int(y), x.rsplit('_', 2)[-2:]),
        reverse=True)
    return backups_list


def create_dir(directory, do_log=True):
    '''
    Creates a directory if it doesn't exists and write the execution
    in the logs
    '''
    expanded_dir_name = os.path.expanduser(directory)
    try:
        if not os.path.isdir(expanded_dir_name):
            if do_log:
                logging.warning('[*] Directory {0} does not exists,\
                creating...'.format(expanded_dir_name))
            os.makedirs(expanded_dir_name)
        else:
            if do_log:
                logging.warning('[*] Directory {0} found!'.format(
                    expanded_dir_name))
    except Exception as error:
        err = '[*] Error while creating directory {0}: {1}\
            '.format(expanded_dir_name, error)
        raise Exception(err)


def get_match_backup(backup_opt_dict):
    '''
    Return a dictionary containing a list of remote matching backups from
    backup_opt_dict.remote_obj_list.
    Backup have to exactly match against backup name and hostname of the
    node where freezer is executed. The matching objects are stored and
    available in backup_opt_dict.remote_match_backup
    '''

    if not backup_opt_dict.backup_name or not backup_opt_dict.container \
            or not backup_opt_dict.remote_obj_list:
        raise Exception("[*] Error: please provide a valid Swift container,\
            backup name and the container contents")

    backup_name = backup_opt_dict.backup_name.lower()
    if backup_opt_dict.remote_obj_list:
        hostname = backup_opt_dict.hostname
        for container_object in backup_opt_dict.remote_obj_list:
            object_name = container_object.get('name', None)
            if object_name:
                obj_name_match = re.search(r'{0}_({1})_\d+?_\d+?$'.format(
                    hostname, backup_name), object_name.lower(), re.I)
                if obj_name_match:
                    backup_opt_dict.remote_match_backup.append(
                        object_name)
                    backup_opt_dict.remote_objects.append(container_object)

    return backup_opt_dict


def get_newest_backup(backup_opt_dict):
    '''
    Return from backup_opt_dict.remote_match_backup, the newest backup
    matching the provided backup name and hostname of the node where
    freezer is executed. It correspond to the previous backup executed.
    NOTE: If backup has no tar_metadata, no newest backup is returned.
    '''

    if not backup_opt_dict.remote_match_backup:
        return backup_opt_dict

    backup_timestamp = 0
    hostname = backup_opt_dict.hostname
    # Sort remote backup list using timestamp in reverse order,
    # that is from the newest to the oldest executed backup
    sorted_backups_list = sort_backup_list(backup_opt_dict)
    for remote_obj in sorted_backups_list:
        obj_name_match = re.search(r'^{0}_({1})_(\d+)_\d+?$'.format(
            hostname, backup_opt_dict.backup_name), remote_obj, re.I)
        if not obj_name_match:
            continue
        remote_obj_timestamp = int(obj_name_match.group(2))
        if remote_obj_timestamp > backup_timestamp:
            backup_timestamp = remote_obj_timestamp
            break

    tar_metadata_obj = 'tar_metadata_{0}'.format(remote_obj)
    if tar_metadata_obj in sorted_backups_list:
        backup_opt_dict.remote_newest_backup = remote_obj

    return backup_opt_dict


def get_rel_oldest_backup(backup_opt_dict):
    '''
    Return from swift, the relative oldest backup matching the provided
    backup name and hostname of the node where freezer is executed.
    The relative oldest backup correspond the oldest backup from the
    last level 0 backup.
    '''

    if not backup_opt_dict.backup_name:
        err = "[*] Error: please provide a valid backup name in \
            backup_opt_dict.backup_name"
        logging.exception(err)
        raise Exception(err)

    backup_opt_dict.remote_rel_oldest = u''
    backup_name = backup_opt_dict.backup_name
    hostname = backup_opt_dict.hostname
    first_backup_name = False
    first_backup_ts = 0
    for container_object in backup_opt_dict.remote_obj_list:
        object_name = container_object.get('name', None)
        if not object_name:
            continue
        obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
            hostname, backup_name), object_name, re.I)
        if not obj_name_match:
            continue
        remote_obj_timestamp = int(obj_name_match.group(2))
        remote_obj_level = int(obj_name_match.group(3))
        if remote_obj_level == 0 and (remote_obj_timestamp > first_backup_ts):
            first_backup_name = object_name
            first_backup_ts = remote_obj_timestamp

    backup_opt_dict.remote_rel_oldest = first_backup_name
    return backup_opt_dict


def eval_restart_backup(backup_opt_dict):
    '''
    Restart backup level if the first backup execute with always_level
    is older then restart_always_level
    '''

    if not backup_opt_dict.restart_always_level:
        logging.info('[*] No need to set Backup {0} to level 0.'.format(
            backup_opt_dict.backup_name))
        return False

    logging.info('[*] Checking always backup level timestamp...')
    # Compute the amount of seconds to be compared with
    # the remote backup timestamp
    max_time = int(float(backup_opt_dict.restart_always_level) * 86400)
    current_timestamp = backup_opt_dict.time_stamp
    backup_name = backup_opt_dict.backup_name
    hostname = backup_opt_dict.hostname
    # Get relative oldest backup by calling get_rel_oldes_backup()
    backup_opt_dict = get_rel_oldest_backup(backup_opt_dict)
    if not backup_opt_dict.remote_rel_oldest:
        logging.info('[*] Relative oldest backup for backup name {0} on \
            host {1} not available. The backup level is NOT restarted'.format(
            backup_name, hostname))
        return False

    obj_name_match = re.search(r'{0}_({1})_(\d+)_(\d+?)$'.format(
        hostname, backup_name), backup_opt_dict.remote_rel_oldest, re.I)
    if not obj_name_match:
        err = ('[*] No backup match available for backup {0} '
               'and host {1}'.format(backup_name, hostname))
        logging.info(err)
        return Exception(err)

    first_backup_ts = int(obj_name_match.group(2))
    if (current_timestamp - first_backup_ts) > max_time:
        logging.info(
            '[*] Backup {0} older then {1} days. Backup level set to 0'.format(
                backup_name, backup_opt_dict.restart_always_level))

        return True
    else:
        logging.info('[*] No need to set level 0 for Backup {0}.'.format(
            backup_name))

    return False


class DateTime(object):
    def __init__(self, value):
        if isinstance(value, int):
            self.date_time = datetime.datetime.fromtimestamp(value)
        elif isinstance(value, datetime.datetime):
            self.date_time = value
        else:
            fmt = '%Y-%m-%dT%H:%M:%S'
            try:
                self.date_time = datetime.datetime.strptime(value, fmt)
            except:
                raise Exception('bad datetime format: "{0}'.format(value))

    @property
    def timestamp(self):
        return int(time.mktime(self.date_time.timetuple()))

    def __repr__(self):
        return self.date_time.strftime('%Y-%m-%d %H:%M:%S')

    def __sub__(self, other):
        assert isinstance(other, DateTime)
        return self.date_time - other.date_time  # return timedelta

    @staticmethod
    def now():
        return DateTime(datetime.datetime.now())


def set_backup_level(backup_opt_dict, manifest_meta_dict):
    '''
    Set the backup level params in backup_opt_dict and the swift
    manifest. This is a fundamental part of the incremental backup
    '''

    if manifest_meta_dict.get('x-object-meta-backup-name'):
        backup_opt_dict.curr_backup_level = int(
            manifest_meta_dict.get('x-object-meta-backup-current-level'))
        max_level = manifest_meta_dict.get(
            'x-object-meta-maximum-backup-level')
        always_level = manifest_meta_dict.get(
            'x-object-meta-always-backup-level')
        restart_always_level = manifest_meta_dict.get(
            'x-object-meta-restart-always-backup')
        if max_level:
            max_level = int(max_level)
            if backup_opt_dict.curr_backup_level < max_level:
                backup_opt_dict.curr_backup_level += 1
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    str(backup_opt_dict.curr_backup_level)
            else:
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    backup_opt_dict.curr_backup_level = '0'
        elif always_level:
            always_level = int(always_level)
            if backup_opt_dict.curr_backup_level < always_level:
                backup_opt_dict.curr_backup_level += 1
                manifest_meta_dict['x-object-meta-backup-current-level'] = \
                    str(backup_opt_dict.curr_backup_level)
            # If restart_always_level is set, the backup_age will be computed
            # and if the backup age in days is >= restart_always_level, then
            # backup-current-level will be set to 0
            if restart_always_level:
                backup_opt_dict.restart_always_level = restart_always_level
                if eval_restart_backup(backup_opt_dict):
                    backup_opt_dict.curr_backup_level = '0'
                    manifest_meta_dict['x-object-meta-backup-current-level'] \
                        = '0'
    else:
        backup_opt_dict.curr_backup_level = \
            manifest_meta_dict['x-object-meta-backup-current-level'] = '0'

    return backup_opt_dict, manifest_meta_dict


def get_vol_fs_type(backup_opt_dict):
    '''
    The argument need to be a full path lvm name i.e. /dev/vg0/var
    or a disk partition like /dev/sda1. The returnet value is the
    file system type
    '''

    vol_name = backup_opt_dict.lvm_srcvol
    if os.path.exists(vol_name) is False:
        err = '[*] Provided volume name not found: {0} '.format(vol_name)
        logging.exception(err)
        raise Exception(err)

    file_cmd = '{0} -0 -bLs --no-pad --no-buffer --preserve-date \
    {1}'.format(backup_opt_dict.file_path, vol_name)
    file_process = subprocess.Popen(
        file_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True,
        executable=backup_opt_dict.bash_path)
    (file_out, file_err) = file_process.communicate()
    file_match = re.search(r'(\S+?) filesystem data', file_out, re.I)
    if file_match is None:
        err = '[*] File system type not guessable: {0}'.format(file_err)
        logging.exception(err)
        raise Exception(err)
    else:
        filesys_type = file_match.group(1)
        logging.info('[*] File system {0} found for volume {1}'.format(
            filesys_type, vol_name))
        return filesys_type.lower().strip()


def check_backup_and_tar_meta_existence(backup_opt_dict):
    '''
    Check if any backup is already available on Swift.
    The verification is done by backup_name, which needs to be unique
    in Swift. This function will return an empty dict if no backup are
    found or the Manifest metadata if the backup_name is available
    '''

    if not backup_opt_dict.backup_name or not backup_opt_dict.container or \
            not backup_opt_dict.remote_obj_list:
        logging.warning(
            ('[*] A valid Swift container, or backup name or container '
             'content not available. Level 0 backup is being executed '))
        return dict()

    logging.info("[*] Retrieving backup name {0} on container \
    {1}".format(
        backup_opt_dict.backup_name.lower(), backup_opt_dict.container))
    backup_opt_dict = get_match_backup(backup_opt_dict)
    backup_opt_dict = get_newest_backup(backup_opt_dict)

    if backup_opt_dict.remote_newest_backup:
        swift = backup_opt_dict.client_manager.get_swift()
        logging.info("[*] Backup {0} found!".format(
            backup_opt_dict.backup_name))
        backup_match = swift.head_object(
            backup_opt_dict.container, backup_opt_dict.remote_newest_backup)

        return backup_match
    else:
        logging.warning("[*] No such backup {0} available... Executing \
            level 0 backup".format(backup_opt_dict.backup_name))
        return dict()


def add_host_name_ts_level(backup_opt_dict, time_stamp=int(time.time())):
    '''
    Create the object name as:
    hostname_backupname_timestamp_backup_level
    '''

    if backup_opt_dict.backup_name is False:
        err = ('[*] Error: Please specify the backup name with '
               '--backup-name option')
        logging.exception(err)
        raise Exception(err)

    backup_name = u'{0}_{1}_{2}_{3}'.format(
        backup_opt_dict.hostname,
        backup_opt_dict.backup_name,
        time_stamp, backup_opt_dict.curr_backup_level)

    return backup_name


def get_mount_from_path(path):
    """
    Take a file system path as argument and return the mount point
    for that file system path.

    :param path: file system path
    :returns: mount point of path
    """

    if not os.path.exists(path):
        logging.critical('[*] Error: provided path does not exist')
        raise IOError

    mount_point_path = os.path.abspath(path)
    while not os.path.ismount(mount_point_path):
        mount_point_path = os.path.dirname(mount_point_path)

    return mount_point_path


# see: http://goo.gl/kTQMs
HUMAN_2_SYMBOLS = {
    'customary': ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext': ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                      'zetta', 'iotta'),
    'iec': ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext': ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                'zebi', 'yobi'),
}


def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.
    """

    if s in (False, None, '-1'):
        return -1

    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in HUMAN_2_SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = HUMAN_2_SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]: 1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i + 1) * 10
    return int(num * prefix[letter])


def create_subprocess(cmd):
    """
    Create a new subprocess in the OS
    :param cmd: command to execute in the subprocess
    :return: the output and errors of the subprocess
    """
    process = subprocess.Popen(cmd,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    return process.communicate()


def date_to_timestamp(date):
    fmt = '%Y-%m-%dT%H:%M:%S'
    opt_backup_date = datetime.datetime.strptime(date, fmt)
    return int(time.mktime(opt_backup_date.timetuple()))


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __getattr__(self, item):
        return self.__dict__.get(item)


class ReSizeStream:
    """
    Iterator/File-like object for changing size of chunk in stream
    """
    def __init__(self, stream, length, chunk_size):
        self.stream = stream
        self.length = length
        self.chunk_size = chunk_size
        self.reminder = ""
        self.transmitted = 0

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def next(self):
        logging.info("Transmitted (%s) of (%s)" % (self.transmitted,
                                                   self.length))
        chunk_size = self.chunk_size
        if len(self.reminder) > chunk_size:
            result = self.reminder[:chunk_size]
            self.reminder = self.reminder[chunk_size:]
            self.transmitted += len(result)
            return result
        else:
            stop = False
            while not stop and len(self.reminder) < chunk_size:
                try:
                    self.reminder += next(self.stream)
                except StopIteration:
                    stop = True
            if stop:
                result = self.reminder
                if len(self.reminder) == 0:
                    raise StopIteration()
                self.reminder = []
                self.transmitted += len(result)
                return result
            else:
                result = self.reminder[:chunk_size]
                self.reminder = self.reminder[chunk_size:]
                self.transmitted += len(result)
                return result

    def read(self, chunk_size):
        self.chunk_size = chunk_size
        return self.next()
