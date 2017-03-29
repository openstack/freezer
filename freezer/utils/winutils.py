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
import json
import os
import sys


def is_windows():
    """
    :return: True if the running platform is windows
    """
    return True if sys.platform == 'win32' else False


class DisableFileSystemRedirection(object):
    """
    When a 32 bit program runs on a 64 bit operating system the paths
    to C:/Windows/System32 automatically get redirected to the 32 bit
    version (C:/Windows/SysWow64), if you really do need to access the
    contents of System32, you need to disable the file system redirector first.
    """

    def __init__(self):
        if is_windows():
            self._disable = (ctypes.windll.kernel32.
                             Wow64DisableWow64FsRedirection)
            self._revert = (ctypes.windll.kernel32.
                            Wow64RevertWow64FsRedirection)
        else:
            raise Exception("Useless if not windows")

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


def save_environment(home):
    """Read the environment from the terminal where the scheduler is
    initialized and save the environment variables to be reused within the
    windows service
    """
    env_path = os.path.join(home, 'env.json')
    with open(env_path, 'wb') as tmp:
        json.dump(os.environ.copy(), tmp)


def set_environment(home):
    """Read the environment variables saved by the win_daemon and restore it
    here for the windows service
    """
    json_env = os.path.join(home, 'env.json')
    with open(json_env, 'rb') as fp:
        env = json.loads(fp.read())
        for k, v in env.items():
            os.environ[str(k).strip()] = str(v).strip()
