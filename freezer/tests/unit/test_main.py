# (c) Copyright 2026 Alvaro Soto <alsotoes@gmail.com>
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


import unittest
from unittest import mock

from freezer.main import run_job


class TestRunJob(unittest.TestCase):

    def _make_conf(self, action='backup', action_extra=None):
        conf = mock.Mock()
        conf.action = action
        conf.quiet = True
        conf.metadata_out = None
        conf.engine = mock.Mock()
        conf.hostname_backup_name = 'host_test'
        conf.backup_name = 'test_backup'
        conf.remove_before_date = None
        conf.remove_from_date = None
        conf.remove_older_than = None
        if action_extra:
            for k, v in action_extra.items():
                setattr(conf, k, v)
        return conf

    def test_backup_with_remove_older_than_triggers_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'backup',
            'remove_older_than': 1,
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_backup_job = mock.Mock()
            mock_backup_job.execute.return_value = None
            mock_job.BackupJob = mock.Mock(return_value=mock_backup_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.BackupJob.assert_called_once_with(conf, storage)
            mock_backup_job.execute.assert_called_once()
            mock_job.AdminJob.assert_called_once_with(conf, storage)
            mock_admin_job.execute.assert_called_once()

    def test_backup_with_remove_older_than_zero_triggers_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'backup',
            'remove_older_than': 0,
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_backup_job = mock.Mock()
            mock_backup_job.execute.return_value = None
            mock_job.BackupJob = mock.Mock(return_value=mock_backup_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.AdminJob.assert_called_once_with(conf, storage)
            mock_admin_job.execute.assert_called_once()

    def test_backup_with_remove_before_date_triggers_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'backup',
            'remove_before_date': '2016-07-05T18:00:00',
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_backup_job = mock.Mock()
            mock_backup_job.execute.return_value = None
            mock_job.BackupJob = mock.Mock(return_value=mock_backup_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.AdminJob.assert_called_once_with(conf, storage)
            mock_admin_job.execute.assert_called_once()

    def test_backup_with_remove_from_date_triggers_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'backup',
            'remove_from_date': '2016-07-05T18:00:00',
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_backup_job = mock.Mock()
            mock_backup_job.execute.return_value = None
            mock_job.BackupJob = mock.Mock(return_value=mock_backup_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.AdminJob.assert_called_once_with(conf, storage)
            mock_admin_job.execute.assert_called_once()

    def test_backup_without_removal_options_skips_admin_job(self):
        conf = self._make_conf(action='backup')
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_backup_job = mock.Mock()
            mock_backup_job.execute.return_value = None
            mock_job.BackupJob = mock.Mock(return_value=mock_backup_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.AdminJob.assert_not_called()

    def test_restore_with_remove_older_than_triggers_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'restore',
            'remove_older_than': 1,
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_restore_job = mock.Mock()
            mock_restore_job.execute.return_value = None
            mock_job.RestoreJob = mock.Mock(return_value=mock_restore_job)
            mock_admin_job = mock.Mock()
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_job)

            run_job(conf, storage)

            mock_job.AdminJob.assert_called_once_with(conf, storage)
            mock_admin_job.execute.assert_called_once()

    def test_admin_action_skips_extra_admin_job(self):
        conf = self._make_conf(action_extra={
            'action': 'admin',
            'remove_older_than': 1,
        })
        storage = mock.Mock()

        with mock.patch('freezer.main.job') as mock_job:
            mock_admin_run = mock.Mock()
            mock_admin_run.execute.return_value = None
            mock_job.AdminJob = mock.Mock(return_value=mock_admin_run)

            run_job(conf, storage)

            # AdminJob should only be called once (the regular dispatch),
            # not again via the hook
            mock_job.AdminJob.assert_called_once_with(conf, storage)
