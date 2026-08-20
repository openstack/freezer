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

    @staticmethod
    def get_freezer_backup_id(backup):
        meta = getattr(backup, 'metadata', {}) or {}
        return meta.get('freezer_backup_id')

    @staticmethod
    def is_freezer_backup(backup):
        meta = getattr(backup, 'metadata', {}) or {}
        return meta.get('created_by') == 'freezer'

    def _delete_single_backup(self, backup_id):
        cinder_client = self.cinder_client
        cinder_backup = None
        freezer_backup_id = None
        try:
            cinder_backup = cinder_client.get_backup(backup_id)
        except Exception as e:
            LOG.warning(
                "Could not fetch cinder backup %s details: %s", backup_id, e
            )

        if cinder_backup:
            freezer_backup_id = self.get_freezer_backup_id(cinder_backup)

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

        return freezer_backup_id

    def del_cinderbackup_and_dependend_incremental(self, backup_id):
        """
        :param backup_id: backup_id  of cinder volume
        :return: list of deleted freezer_backup_ids
        """
        cinder_client = self.cinder_client
        backup = cinder_client.get_backup(backup_id)
        if not backup:
            LOG.warning("Backup %s not found", backup_id)
            return []
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

        deleted_freezer_ids = []
        if target_idx != -1:
            dependents = []
            for b in sorted_backups[target_idx + 1:]:
                if b.is_incremental:
                    dependents.append(b)
                else:
                    break

            for dep in reversed(dependents):
                fid = self._delete_single_backup(dep.id)
                if fid:
                    deleted_freezer_ids.append(fid)

        fid = self._delete_single_backup(backup_id)
        if fid:
            deleted_freezer_ids.append(fid)
        return deleted_freezer_ids

    def del_off_limit_fullbackup(self, volume_id, keep_number,
                                 freezer_only=True):
        """
        :param volume_id: id of Volume
        :param keep_number: int  keep number of fullbackup
        :param freezer_only: bool whether to only rotate backups created by
                             Freezer
        :return: list of deleted freezer_backup_ids
        """
        keep_full_backup_num = int(keep_number)
        cinder_client = self.cinder_client
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
            'is_incremental': False,
            'sort_key': 'created_at',
            'sort_dir': 'asc',
            'details': True,
        }
        fullbackups = list(cinder_client.backups(**search_opts))
        if freezer_only:
            fullbackups = [b for b in fullbackups if self.is_freezer_backup(b)]

        if len(fullbackups) <= keep_full_backup_num:
            LOG.info("The numbers of %s fullbackup is %d,"
                     "but keep-number-of-fullbackup is %d,"
                     "don't need delete old backups."
                     % (volume_id, len(fullbackups), keep_full_backup_num))
            return []
        deleted_ids = []
        for fullbackup in fullbackups[:-keep_full_backup_num]:
            dids = self.del_cinderbackup_and_dependend_incremental(
                fullbackup.id)
            if dids:
                deleted_ids.extend(dids)
        return deleted_ids

    def remove_cinderbackup_older_than(self, volume_id,
                                       remove_older_timestamp,
                                       freezer_only=True):
        """Removes backups older than or equal to timestamp in a chain-safe manner.

        :param volume_id: id of Volume
        :param remove_older_timestamp: int
        :param freezer_only: bool whether to only remove backups created
            by Freezer
        :return: list of deleted freezer_backup_ids
        """
        cinder_client = self.cinder_client
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
            'sort_key': 'created_at',
            'sort_dir': 'asc',
            'details': True,
        }
        backups = cinder_client.backups(**search_opts)
        deleted_ids = []
        chains = []
        current_chain = None
        for backup in backups:
            if not getattr(backup, 'is_incremental', False):
                current_chain = {'full': backup, 'increments': []}
                chains.append(current_chain)
            elif current_chain is not None:
                current_chain['increments'].append(backup)

        for chain in chains:
            full_backup = chain['full']
            increments = chain['increments']
            if freezer_only and not self.is_freezer_backup(full_backup):
                LOG.debug("Skipping non-freezer full backup %s",
                          full_backup.id)
                continue

            latest_backup = full_backup
            if increments:
                latest_backup = increments[-1]

            created_at = getattr(latest_backup, 'created_at', None)
            if not created_at:
                LOG.debug("Backup %s has no created_at timestamp; "
                          "skipping chain", latest_backup.id)
                continue

            try:
                latest_timestamp = timeutils.parse_isotime(
                    created_at).timestamp()
            except (ValueError, TypeError) as err:
                LOG.warning("Failed to parse created_at '%s' for backup %s: "
                            "%s; skipping chain", created_at,
                            latest_backup.id, err)
                continue

            if latest_timestamp <= remove_older_timestamp:
                for inc in reversed(increments):
                    if freezer_only and not self.is_freezer_backup(inc):
                        LOG.debug("Skipping non-freezer incremental backup %s",
                                  inc.id)
                        continue
                    fid = self._delete_single_backup(inc.id)
                    if fid:
                        deleted_ids.append(fid)
                fid = self._delete_single_backup(full_backup.id)
                if fid:
                    deleted_ids.append(fid)
            else:
                LOG.info("Incremental backup chain for volume %s has active "
                         "increments; preserving chain until all increments "
                         "expire.", volume_id)

        return deleted_ids
