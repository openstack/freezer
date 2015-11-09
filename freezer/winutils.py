# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import ctypes
import logging
import sys

from freezer.utils import create_subprocess


def is_windows():
    """
    :return: True if the running platform is windows
    """
    return True if sys.platform == 'win32' else False


class DisableFileSystemRedirection:
    """
    When a 32 bit program runs on a 64 bit operating system the paths
    to C:/Windows/System32 automatically get redirected to the 32 bit
    version (C:/Windows/SysWow64), if you really do need to access the
    contents of System32, you need to disable the file system redirector first.
    """
    if is_windows():
        _disable = ctypes.windll.kernel32.Wow64DisableWow64FsRedirection
        _revert = ctypes.windll.kernel32.Wow64RevertWow64FsRedirection
    else:
        _disable = ''
        _revert = ''

    def __enter__(self):
        self.old_value = ctypes.c_long()
        self.success = self._disable(ctypes.byref(self.old_value))

    def __exit__(self, type, value, traceback):
        if self.success:
            self._revert(self.old_value)


def use_shadow(to_backup, windows_volume):
    """ add the shadow path to the backup directory """
    return to_backup.replace(windows_volume, '{0}freezer_shadowcopy\\'
                             .format(windows_volume))


def clean_tar_command(tar_cmd):
    """ Delete tar arguments that are not supported by GnuWin32 tar"""
    tar_cmd = tar_cmd.replace('--hard-dereference', '')
    tar_cmd = tar_cmd.replace('--no-check-device', '')
    tar_cmd = tar_cmd.replace('--warning=none', '')
    tar_cmd = tar_cmd.replace('--seek', '')
    tar_cmd = tar_cmd.replace('-z', '')
    return tar_cmd


def add_gzip_to_command(tar_cmd):
    gzip_cmd = 'gzip -7'
    return '{0} | {1}'.format(tar_cmd, gzip_cmd)


def stop_sql_server(sql_server_instance):
    """ Stop a SQL Server instance to perform the backup of the db files """

    logging.info('[*] Stopping SQL Server for backup')
    with DisableFileSystemRedirection():
        cmd = 'net stop "SQL Server ({0})"'\
            .format(sql_server_instance)
        (out, err) = create_subprocess(cmd)
        if err != '':
            raise Exception('[*] Error while stopping SQL Server,'
                            ', error {0}'.format(err))


def start_sql_server(sql_server_instance):
    """ Start the SQL Server instance after the backup is completed """

    with DisableFileSystemRedirection():
        cmd = 'net start "SQL Server ({0})"'.format(sql_server_instance)
        (out, err) = create_subprocess(cmd)
        if err != '':
            raise Exception('[*] Error while starting SQL Server'
                            ', error {0}'.format(err))
        logging.info('[*] SQL Server back to normal')
