# Copyright 2014 Hewlett-Packard
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
#
# This product includes cryptographic software written by Eric Young
# (eay@cryptsoft.com). This product includes software written by Tim
# Hudson (tjh@cryptsoft.com).
# ========================================================================

import sys
import ctypes


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


def use_shadow(to_backup, volume):
    """ add the shadow path to the backup directory """
    return to_backup.replace(volume, '{0}shadowcopy\\'.format(volume))


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
