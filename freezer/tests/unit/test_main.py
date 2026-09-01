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

from unittest import mock

from freezer.main import freezer_main
from freezer.main import run_job
from freezer.tests import commons


class TestRunJob(commons.FreezerBaseTestCase):

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


class TestFreezerMain(commons.FreezerBaseTestCase):

    def _make_backup_args(self, mode='cindernative',
                          backup_media='cindernative'):
        args = commons.BackupOpt1()
        args.quiet = True
        args.max_priority = False
        args.mode = mode
        args.backup_media = backup_media
        args.storages = None
        args.storage = 'swift'
        args.max_segment_size = 33554432
        args.rsync_block_size = 4096
        return args

    @mock.patch('freezer.main.client_manager')
    @mock.patch('freezer.main.storage_from_dict')
    @mock.patch('freezer.main.engine_manager')
    @mock.patch('freezer.main.run_job')
    def test_freezer_main_cindernative_skips_storage_init(
            self, mock_run_job, mock_engine_mgr, mock_storage_from_dict,
            mock_client_mgr):
        args = self._make_backup_args(mode='cindernative',
                                      backup_media='cindernative')
        freezer_main(args)

        mock_storage_from_dict.assert_not_called()
        mock_engine_mgr.EngineManager.assert_not_called()
        mock_run_job.assert_called_once_with(args, None)
        self.assertIsNone(args.engine)

    @mock.patch('freezer.main.client_manager')
    @mock.patch('freezer.main.storage_from_dict')
    @mock.patch('freezer.main.engine_manager')
    @mock.patch('freezer.main.run_job')
    def test_freezer_main_non_cindernative_initializes_storage(
            self, mock_run_job, mock_engine_mgr, mock_storage_from_dict,
            mock_client_mgr):
        args = self._make_backup_args(mode='fs', backup_media='fs')
        fake_storage = mock.Mock()
        mock_storage_from_dict.return_value = fake_storage

        freezer_main(args)

        mock_storage_from_dict.assert_called_once()
        mock_engine_mgr.EngineManager.assert_called_once()
        mock_run_job.assert_called_once_with(args, fake_storage)
