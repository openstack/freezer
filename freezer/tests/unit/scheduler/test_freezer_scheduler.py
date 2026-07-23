# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import unittest
from unittest import mock

from freezer.scheduler import freezer_scheduler
from freezer.tests.unit.scheduler.commons import set_default_capabilities
from freezer.tests.unit.scheduler.commons import set_test_capabilities

SUPPORTED_JOB = {
    'job_id': 'test2',
    'job_schedule': {},
    'job_actions': [
        {'freezer_action': {'action': 'backup'}},
    ],
}
UNSUPPORTED_JOB = {
    'job_id': 'test1',
    'job_schedule': {},
    'job_actions': [
        {'freezer_action': {'action': 'exec'}},
    ],
}


class TestFreezerScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = freezer_scheduler.FreezerScheduler(
            apiclient=mock.MagicMock(),
            interval=1,
            job_path='/tmp/test',
        )
        set_test_capabilities()

    def tearDown(self):
        set_default_capabilities()

    def test_filter_jobs(self):
        job_doc_list = [
            SUPPORTED_JOB,
            UNSUPPORTED_JOB,
        ]
        expected_jobs = [SUPPORTED_JOB]
        filtered_jobs = self.scheduler.filter_jobs(job_doc_list)
        self.assertListEqual(filtered_jobs, expected_jobs)

    def test_update_auth_options(self):
        mock_conf = mock.Mock()
        mock_conf.service_auth = mock.Mock()
        opts = mock.Mock()
        with mock.patch('freezer.scheduler.arguments.build_os_options') as \
                mock_build_os_options:
            opt = mock.Mock()
            opt.dest = 'os_username'
            mock_build_os_options.return_value = [opt]
            # Case 1: CONF has no value (empty string/None),
            # service_auth has value.
            # Should take from service_auth.
            mock_conf.service_auth.os_username = 'service_user'
            freezer_scheduler.update_auth_options(mock_conf, opts)
            self.assertEqual('service_user', opts.os_username)

            # Case 2: CONF has value (CLI/Env), service_auth has value.
            # Should prefer CONF value, so opts is NOT updated
            # (client gets it from CONF directly via opts.opts)
            mock_conf.service_auth.os_username = None
            opts = mock.Mock(spec=[])
            freezer_scheduler.update_auth_options(mock_conf, opts)
            self.assertFalse(hasattr(opts, 'os_username'))

    def test_filter_jobs_centralized(self):
        from freezer.scheduler.freezer_scheduler import CONF
        CONF.scheduler.centralized_scheduler = True
        job1 = {'job_id': 'job1', 'user_credentials': {'trust_id': 'trust1'}}
        job2 = {'job_id': 'job2', 'user_credentials': {}}
        job_doc_list = [job1, job2]

        patch_path = 'freezer.scheduler.scheduler_job.Job.check_capabilities'
        with mock.patch(patch_path) as mock_check:
            mock_check.return_value = True
            filtered = self.scheduler.filter_jobs(job_doc_list)
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]['job_id'], 'job1')
        CONF.scheduler.centralized_scheduler = False

    def test_owns_job_standalone_is_always_true(self):
        # No coordinator configured -> behaves as today.
        self.assertTrue(self.scheduler.owns_job('any-job'))

    def test_owns_job_delegates_to_coordinator(self):
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = False
        self.assertFalse(self.scheduler.owns_job('j1'))
        self.scheduler.coordinator.is_owner.assert_called_once_with('j1')

    def test_job_lock_standalone_grants_run(self):
        with self.scheduler.job_lock('j1') as may_run:
            self.assertTrue(may_run)

    def test_poll_skips_jobs_not_owned(self):
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = False
        job_doc = {'job_id': 'j1', 'job_schedule': {'event': ''}}
        with mock.patch.object(self.scheduler, 'get_jobs',
                               return_value=[job_doc]), \
                mock.patch.object(self.scheduler, 'create_job') as mock_create:
            self.scheduler.poll()
            mock_create.assert_not_called()
        self.assertNotIn('j1', self.scheduler.jobs)

    def test_poll_runs_jobs_owned(self):
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = True
        job_doc = {'job_id': 'j1', 'job_schedule': {'event': ''}}
        fake_job = mock.MagicMock()
        with mock.patch.object(self.scheduler, 'get_jobs',
                               return_value=[job_doc]), \
                mock.patch.object(self.scheduler, 'create_job',
                                  return_value=fake_job) as mock_create:
            self.scheduler.poll()
            mock_create.assert_called_once_with(job_doc)
            fake_job.process_event.assert_called_once_with(job_doc)

    def test_poll_unschedules_job_when_ownership_lost(self):
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = False
        # We used to own j1 and have it scheduled locally (not running).
        local_job = mock.MagicMock()
        local_job.is_running.return_value = False
        self.scheduler.jobs = {'j1': local_job}
        job_doc = {'job_id': 'j1', 'job_schedule': {'event': ''}}
        with mock.patch.object(self.scheduler, 'get_jobs',
                               return_value=[job_doc]):
            self.scheduler.poll()
        local_job.unschedule.assert_called_once()
        self.assertNotIn('j1', self.scheduler.jobs)

    def test_poll_keeps_running_job_despite_ownership_loss(self):
        # A member still executing a job keeps handling its events (e.g.
        # abort) until the run ends, even if the ring moved the job away.
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = False
        local_job = mock.MagicMock()
        local_job.is_running.return_value = True
        local_job.can_be_removed.return_value = False
        self.scheduler.jobs = {'j1': local_job}
        job_doc = {'job_id': 'j1', 'job_schedule': {'event': ''}}
        with mock.patch.object(self.scheduler, 'get_jobs',
                               return_value=[job_doc]):
            self.scheduler.poll()
        local_job.unschedule.assert_not_called()
        local_job.process_event.assert_called_once_with(job_doc)
        self.assertIn('j1', self.scheduler.jobs)

    def test_poll_abort_only_kills_locally_running_job(self):
        # In clustered mode current_pid may belong to another member's
        # host: a member must not kill that pid unless it runs the job.
        self.scheduler.coordinator = mock.MagicMock()
        self.scheduler.coordinator.is_owner.return_value = True
        local_job = mock.MagicMock()
        self.scheduler.jobs = {'j1': local_job}
        job_doc = {'job_id': 'j1',
                   'job_schedule': {'event': 'abort', 'current_pid': 4242}}
        term_path = 'freezer.scheduler.utils.terminate_subprocess'
        for running, expect_kill in ((False, False), (True, True)):
            local_job.is_running.return_value = running
            self.scheduler.jobs = {'j1': local_job}
            with mock.patch.object(self.scheduler, 'get_jobs',
                                   return_value=[job_doc]), \
                    mock.patch(term_path) as mock_term:
                self.scheduler.poll()
                if expect_kill:
                    mock_term.assert_called_once_with(4242, 'freezer-agent')
                else:
                    mock_term.assert_not_called()

    def test_update_job_metadata_filters_actions(self):
        job_doc = {
            'job_schedule': {'status': 'completed'},
            'session_id': 'session123',
            'session_tag': 1,
            'job_actions': [{'action': 'backup'}]
        }
        with mock.patch.object(self.scheduler, 'update_job') as mock_update:
            self.scheduler.update_job_metadata("test_job_123", job_doc)
            mock_update.assert_called_once()
            called_id, called_doc = mock_update.call_args[0]
            self.assertEqual(called_id, "test_job_123")
            self.assertIn('job_schedule', called_doc)
            self.assertIn('session_id', called_doc)
            self.assertIn('session_tag', called_doc)
            self.assertNotIn('job_actions', called_doc)
