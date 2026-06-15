# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
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


"""
Freezer Admin modes related functions
"""

import time

from oslo_config import cfg
from oslo_log import log
from oslo_service import loopingcall
from oslo_utils import timeutils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class AdminOs(object):
    def __init__(self, client_manager):
        """
        :param client_manager:
        :return:
        """
        self.client_manager = client_manager
        self.cinder_client = self.client_manager.get_cinder()

    def _delete_single_backup(self, backup_id):
        cinder_client = self.cinder_client
        LOG.info("preparing to delete backup %s", backup_id)
        cinder_client.delete_backup(backup_id)

        start_time = int(time.time())

        def wait_del_backup():
            timeout = 120
            del_backup = list(cinder_client.backups(id=backup_id))
            if len(del_backup) == 0:
                LOG.info("Delete backup %s complete" % backup_id)
                raise loopingcall.LoopingCallDone()

            status = del_backup[0].status
            if status in ['error', 'error_deleting']:
                raise Exception("Delete backup %s failed, "
                                "the status of backup is %s."
                                % (backup_id, status))
            if (status == 'deleting') and (int(time.time()) -
                                           start_time > timeout):
                LOG.error("Delete backup %s failed, In a state of "
                          "deleting over 120s", backup_id)
                raise Exception(
                    "Delete backup %s failed due to timeout over 120s, "
                    "the status of backup is %s."
                    % (backup_id, status))
        timer = loopingcall.FixedIntervalLoopingCall(wait_del_backup)
        timer.start(interval=0.5).wait()

    def del_cinderbackup_and_dependend_incremental(self, backup_id):
        """
        :param backup_id: backup_id  of cinder volume
        :return:
        """
        cinder_client = self.cinder_client
        backup = cinder_client.get_backup(backup_id)
        if not backup:
            LOG.warning("Backup %s not found", backup_id)
            return
        sorted_backups = list(cinder_client.backups(
            volume_id=backup.volume_id,
            sort_key='created_at',
            sort_dir='asc'
        ))

        target_idx = -1
        for i, b in enumerate(sorted_backups):
            if b.id == backup_id:
                target_idx = i
                break

        if target_idx != -1:
            dependents = []
            for b in sorted_backups[target_idx + 1:]:
                if b.is_incremental:
                    dependents.append(b)
                else:
                    break

            for dep in reversed(dependents):
                self._delete_single_backup(dep.id)

        self._delete_single_backup(backup_id)

    def del_off_limit_fullbackup(self, volume_id, keep_number):
        """
        :param volume_id: id of Volume
        :param keep_number: int  keep number of fullbackup
        :return:
        """
        keep_full_backup_num = int(keep_number)
        cinder_client = self.cinder_client
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
            'is_incremental': False,
            'sort_key': 'created_at',
            'sort_dir': 'asc',
        }
        fullbackups = list(cinder_client.backups(**search_opts))
        if len(fullbackups) <= keep_full_backup_num:
            LOG.info("The numbers of %s fullbackup is %d,"
                     "but keep-number-of-fullbackup is %d,"
                     "don't need delete old backups."
                     % (volume_id, len(fullbackups), keep_full_backup_num))
            return
        for fullbackup in fullbackups[:-keep_full_backup_num]:
            self.del_cinderbackup_and_dependend_incremental(fullbackup.id)

    def remove_cinderbackup_older_than(self, volume_id,
                                       remove_older_timestamp):
        """
        :param volume_id: id of Volume
        :param remove_older_timestamp: int
        :return:
        """
        cinder_client = self.cinder_client
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
            'sort_key': 'created_at',
            'sort_dir': 'desc',
        }
        backups = cinder_client.backups(**search_opts)
        for backup in backups:
            created_at = getattr(backup, 'created_at', None)
            backup_timestamp = timeutils.parse_isotime(created_at).timestamp()
            if backup_timestamp <= remove_older_timestamp:
                self._delete_single_backup(backup.id)
