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

    def del_cinderbackup_and_dependend_incremental(self, backup_id):
        """
        :param backup_id: backup_id  of cinder volume
        :return:
        """
        cinder_client = self.cinder_client
        search_opts = {
            'parent_id': backup_id
        }
        backups = cinder_client.backups.list(search_opts=search_opts)
        if backups:
            for backup in backups:
                self.del_cinderbackup_and_dependend_incremental(backup.id)
        LOG.info("preparing to delete backup %s", backup_id)
        cinder_client.backups.delete(backup_id)

        start_time = int(time.time())

        def wait_del_backup():
            timeout = 120
            del_backup = cinder_client.backups.list(
                search_opts={'id': backup_id})
            if len(del_backup) == 0:
                LOG.info("Delete backup %s complete" % backup_id)
                raise loopingcall.LoopingCallDone()
            if del_backup[0].status in ['error', 'error_deleting']:
                raise Exception("Delete backup %s failed, "
                                "the status of backup is %s."
                                % (backup_id, del_backup[0].status))
            if (del_backup[0].status == 'deleting') and (int(time.time()) -
                                                         start_time > timeout):
                LOG.error("Delete backup %s failed, In a state of "
                          "deleting over 120s")
                raise Exception(
                    "Delete backup %s failed due to timeout over 120s, "
                    "the status of backup is %s."
                    % (backup_id, del_backup[0].status))
        timer = loopingcall.FixedIntervalLoopingCall(wait_del_backup)
        timer.start(interval=0.5).wait()

    def del_off_limit_fullbackup(self, volume_id, keep_number):
        """
        :param volume_id: id of Volume
        :param keep_number: int  keep number of fullbackup
        :return:
        """
        cinder_client = self.cinder_client
        search_opts = {
            'volume_id': volume_id,
            'status': 'available'
        }
        backups = cinder_client.backups.list(search_opts=search_opts,
                                             sort='created_at:asc')
        # Filter fullbackup
        fullbackups = [backup for backup in backups
                       if not backup.is_incremental]
        if len(fullbackups) <= keep_number:
            LOG.info("The numbers of %s fullbackup is %d,"
                     "but keep-number-of-fullbackup is %d,"
                     "don't need delete old backups."
                     % (volume_id, len(fullbackups), keep_number))
            return
        for fullbackup in fullbackups[:-keep_number]:
            self.del_cinderbackup_and_dependend_incremental(fullbackup.id)
