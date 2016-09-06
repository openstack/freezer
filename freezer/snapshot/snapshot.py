"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Freezer Backup modes related functions
"""

from freezer.snapshot import lvm
from freezer.snapshot import vss
from freezer.utils import winutils


def snapshot_create(backup_opt_dict):
    """
    Calls the code to take fs snapshots, depending on the platform

    :param backup_opt_dict:
    :return: boolean value, True if snapshot has been taken, false otherwise
    """
    if not backup_opt_dict.snapshot:
        return False

    if winutils.is_windows():
        if backup_opt_dict.snapshot:
            # Create a shadow copy.
            backup_opt_dict.shadow_path, backup_opt_dict.shadow = \
                vss.vss_create_shadow_copy(backup_opt_dict.windows_volume)

            backup_opt_dict.path_to_backup = winutils.use_shadow(
                backup_opt_dict.path_to_backup,
                backup_opt_dict.windows_volume)
            return True
        return False
    else:
        return lvm.lvm_snap(backup_opt_dict)


def snapshot_remove(backup_opt_dict, shadow, windows_volume):
    if winutils.is_windows():
        # Delete the shadow copy after the backup
        vss.vss_delete_shadow_copy(shadow, windows_volume)
    else:
        # Unmount and remove lvm snapshot volume
        lvm.lvm_snap_remove(backup_opt_dict)
