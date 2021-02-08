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

import os
import shutil
import tempfile
import unittest

from freezer.scheduler import scheduler_job
from oslo_config import cfg
from unittest import mock

CONF = cfg.CONF


action = {"action": "backup", "storage": "local",
          "mode": "fs", "backup_name": "test",
          "container": "/tmp/backuped",
          "path_to_backup": "/tmp/to_backup"}


class TestSchedulerJob(unittest.TestCase):
    def setUp(self):
        self.job = scheduler_job.Job(None, None, {"job_schedule": {}})

    def test(self):
        scheduler_job.RunningState.stop(self.job, {})

    def test_save_action_to_disk(self):
        with tempfile.NamedTemporaryFile(mode='w',
                                         delete=False) as config_file:
            self.job.save_action_to_file(action, config_file)
            self.assertTrue(os.path.exists(config_file.name))

    def test_save_action_with_none_value_to_disk(self):
        action.update({"log_file": None})
        with tempfile.NamedTemporaryFile(mode='w',
                                         delete=False) as config_file:
            self.job.save_action_to_file(action, config_file)
            self.assertTrue(os.path.exists(config_file.name))

    def test_save_action_with_bool_value_to_disk(self):
        action.update({"no_incremental": False})
        with tempfile.NamedTemporaryFile(mode='w',
                                         delete=False) as config_file:
            self.job.save_action_to_file(action, config_file)
            self.assertTrue(os.path.exists(config_file.name))


class TestSchedulerJob1(unittest.TestCase):
    def setUp(self):
        self.scheduler = mock.MagicMock()
        self.job_schedule = {"event": "start", "status": "start",
                             "schedule_day": "1"}
        self.jobdoc = {"job_id": "test", "job_schedule": self.job_schedule}
        self.job = scheduler_job.Job(self.scheduler, None, self.jobdoc)

    def test_stopstate_stop(self):
        result = scheduler_job.StopState.stop(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_stopstate_abort(self):
        result = scheduler_job.StopState.abort(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_stopstate_start(self):
        result = scheduler_job.StopState.start(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_stopstate_remove(self):
        result = scheduler_job.StopState.remove(self.job)
        self.assertEqual(result, '')

    def test_scheduledstate_stop(self):
        result = scheduler_job.ScheduledState.stop(self.job, self.jobdoc)
        self.assertEqual(result, 'stop')

    def test_scheduledstate_abort(self):
        result = scheduler_job.ScheduledState.abort(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_scheduledstate_start(self):
        result = scheduler_job.ScheduledState.start(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_scheduledstate_remove(self):
        result = scheduler_job.ScheduledState.remove(self.job)
        self.assertEqual(result, '')

    def test_runningstate_stop(self):
        result = scheduler_job.RunningState.stop(self.job, {})
        self.assertEqual(result, '')

    def test_runningstate_abort(self):
        result = scheduler_job.RunningState.abort(self.job, self.jobdoc)
        self.assertEqual(result, 'aborted')

    def test_runningstate_start(self):
        result = scheduler_job.RunningState.start(self.job, self.jobdoc)
        self.assertEqual(result, '')

    def test_runningstate_remove(self):
        result = scheduler_job.RunningState.remove(self.job)
        self.assertEqual(result, '')

    def test_job_create(self):
        jobdoc = {"job_id": "test", "job_schedule": {"status": "running"}}
        result = scheduler_job.Job.create(None, None, jobdoc)
        self.assertEqual(result.job_doc_status, 'running')
        jobdoc = {"job_id": "test", "job_schedule": {"status": "stop"}}
        result = scheduler_job.Job.create(None, None, jobdoc)
        self.assertEqual(result.event, 'stop')
        jobdoc = {"job_id": "test", "job_schedule": {}}
        result = scheduler_job.Job.create(None, None, jobdoc)
        self.assertEqual(result.event, 'start')

    def test_job_remove(self):
        result = self.job.remove()
        self.assertIsNone(result)

    def test_job_session_id(self):
        self.assertEqual(self.job.session_id, '')
        self.job.session_id = 'test'
        self.assertEqual(self.job.session_id, 'test')

    def test_job_session_tag(self):
        self.assertEqual(self.job.session_tag, 0)
        self.job.session_tag = 1
        self.assertEqual(self.job.session_tag, 1)

    def test_job_result(self):
        self.assertEqual(self.job.result, '')
        self.job.result = 'test'
        self.assertEqual(self.job.result, 'test')

    def test_job_can_be_removed(self):
        result = self.job.can_be_removed()
        self.assertFalse(result)

    def test_save_action_to_file(self):
        action = {'start': "test"}
        temp = tempfile.mkdtemp()
        filename = '/'.join([temp, "test.conf"])
        f = mock.MagicMock()
        f.name = filename
        result = self.job.save_action_to_file(action, f)
        self.assertIsNone(result)
        shutil.rmtree(temp)

    def test_job_schedule_end_date(self):
        self.assertEqual(self.job.schedule_end_date, '')

    def test_job_schedule_cron_fields(self):
        result = self.job.schedule_cron_fields
        self.assertEqual(result, {"day": "1"})

    def test_get_schedule_args(self):
        jobdoc1 = {"job_schedule":
                   {"schedule_start_date": "2020-01-10T10:10:10",
                    "schedule_end_date": "2020-11-10T10:10:10",
                    "schedule_date": "2020-09-10T10:10:10"}}
        job1 = scheduler_job.Job(self.scheduler, None, jobdoc1)
        result = job1.get_schedule_args()
        self.assertEqual(result, {'trigger': 'date',
                                  'run_date': "2020-09-10T10:10:10"})
        jobdoc1 = {"job_schedule":
                   {"schedule_start_date": "2020-10-10T10:10:10",
                    "schedule_end_date": "2020-11-10T10:10:10",
                    "schedule_interval": "continuous"}}
        job1 = scheduler_job.Job(self.scheduler, None, jobdoc1)
        result = job1.get_schedule_args()
        self.assertEqual(result.get('seconds'), 1)
        jobdoc1 = {"job_schedule":
                   {"schedule_start_date": "2020-10-10T10:10:10",
                    "schedule_end_date": "2020-11-10T10:10:10",
                    "schedule_interval": "5 days"}}
        job1 = scheduler_job.Job(self.scheduler, None, jobdoc1)
        result = job1.get_schedule_args()
        self.assertEqual(result.get('days'), 5)
        jobdoc1 = {"job_schedule": {}}
        job1 = scheduler_job.Job(self.scheduler, None, jobdoc1)
        result = job1.get_schedule_args()
        self.assertEqual(result.get('trigger'), 'date')

    def test_job_process_event(self):
        jobdoc1 = {"job_id": "test", "job_schedule": {"event": "start",
                                                      "status": "start"}}
        result = self.job.process_event(jobdoc1)
        self.assertIsNone(result)
        jobdoc1 = {"job_id": "test", "job_schedule": {"event": "stop",
                                                      "status": "start"}}
        result = self.job.process_event(jobdoc1)
        self.assertIsNone(result)
        jobdoc1 = {"job_id": "test", "job_schedule": {"event": "abort",
                                                      "status": "start"}}
        result = self.job.process_event(jobdoc1)
        self.assertIsNone(result)
        jobdoc1 = {"job_id": "test", "job_schedule": {"event": "aborted",
                                                      "status": "start"}}
        result = self.job.process_event(jobdoc1)
        self.assertIsNone(result)

    def test_job_upload_metadata(self):
        metatring = '{"test": "freezer"}'
        self.job.upload_metadata(metatring)
        self.assertTrue(self.scheduler.upload_metadata.called)
        metatring = ''
        result = self.job.upload_metadata(metatring)
        self.assertIsNone(result)

    def test_job_contains_exec(self):
        jobdoc = {'job_actions': [{'freezer_action': {'action': 'exec'}}]}
        job = scheduler_job.Job(None, None, jobdoc)
        result = job.contains_exec()
        self.assertTrue(result)
        jobdoc = {'job_actions': [{'freezer_action': {'action': 'stop'}}]}
        job = scheduler_job.Job(None, None, jobdoc)
        result = job.contains_exec()
        self.assertFalse(result)

    def test_job_update_job_schedule_doc(self):
        jobdoc = {'job_actions': [{'freezer_action': {'action': 'exec'}}]}
        self.job.update_job_schedule_doc(**jobdoc)
        self.assertEqual(self.job.job_doc['job_schedule']['job_actions'],
                         [{'freezer_action': {'action': 'exec'}}])

    @mock.patch('subprocess.Popen')
    def test_job_execute(self, mock_process):
        CONF.disable_exec = True
        scheduler = mock.MagicMock()
        freezer_action = {"backup_name": "freezer",
                          'action': 'exec',
                          "remove_from_date": "2020-11-10T10:10:10"}
        jobdoc = {'job_id': 'test', 'job_schedule': {},
                  'job_actions': [{'freezer_action': freezer_action,
                                   'max_retries_interval': 1,
                                   'max_retries': 1}]}
        job = scheduler_job.Job(scheduler, None, jobdoc)
        result = job.execute()
        self.assertIsNone(result)
        self.assertEqual(job.result, 'fail')

        CONF.disable_exec = False
        process = mock.MagicMock()
        process.pid = 123
        process.communicate.return_value = (b'test', 0)
        process.returncode = -15
        mock_process.return_value = process
        result = job.execute()
        self.assertIsNone(result)
        self.assertEqual(job.result, 'aborted')

        process.communicate.return_value = ('test', 'test')
        process.returncode = 1
        mock_process.return_value = process
        result = job.execute()
        self.assertIsNone(result)
        self.assertEqual(job.result, 'fail')

    def test_job_finish(self):
        scheduler = mock.MagicMock()
        freezer_action = {"backup_name": "freezer",
                          'action': 'exec',
                          "remove_from_date": "2020-11-10T10:10:10"}
        jobdoc = {'job_id': 'test', 'job_schedule': {"event": "remove"},
                  'job_actions': [{'freezer_action': freezer_action,
                                   'max_retries_interval': 1,
                                   'max_retries': 1}]}
        job = scheduler_job.Job(scheduler, None, jobdoc)
        result = job.finish()
        self.assertIsNone(result)
        self.assertEqual(job.job_doc_status, 'removed')

        scheduler.is_scheduled.return_value = False
        jobdoc = {'job_id': 'test', 'job_schedule': {"event": "start"},
                  'job_actions': [{'freezer_action': freezer_action,
                                   'max_retries_interval': 1,
                                   'max_retries': 1}]}
        job = scheduler_job.Job(scheduler, None, jobdoc)
        result = job.finish()
        self.assertIsNone(result)
        self.assertEqual(job.job_doc_status, 'completed')

        scheduler.is_scheduled.return_value = True
        jobdoc = {'job_id': 'test', 'job_schedule': {"event": "stop"},
                  'job_actions': [{'freezer_action': freezer_action,
                                   'max_retries_interval': 1,
                                   'max_retries': 1}]}
        job = scheduler_job.Job(scheduler, None, jobdoc)
        result = job.finish()
        self.assertIsNone(result)
        self.assertEqual(job.job_doc_status, 'completed')

    def test_job_start_session(self):
        scheduler = mock.MagicMock()
        scheduler.start_session.side_effect = [Exception('error'),
                                               {'result': 'success',
                                                'session_tag': 1024}]
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        job.session_id = 'test'
        result = job.start_session()
        self.assertIsNone(result)
        self.assertEqual(job.session_tag, 1024)

        scheduler.start_session.side_effect = [Exception('error'),
                                               Exception('error'),
                                               Exception('error'),
                                               Exception('error'),
                                               Exception('error')]
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        job.session_id = 'test'
        result = job.start_session()
        self.assertIsNone(result)
        self.assertEqual(job.session_tag, 1024)

    def test_job_end_session(self):
        scheduler = mock.MagicMock()
        scheduler.end_session.side_effect = [Exception('error'),
                                             {'result': 'success'}]
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        job.session_id = 'test'
        result = job.end_session('test')
        self.assertIsNone(result)
        self.assertEqual(job.session_tag, 0)

        scheduler.end_session.side_effect = [Exception('error'),
                                             Exception('error'),
                                             Exception('error'),
                                             Exception('error'),
                                             Exception('error')]
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        job.session_id = 'test'
        result = job.end_session('test')
        self.assertIsNone(result)
        self.assertEqual(job.session_tag, 0)

    def test_job_schedule(self):
        scheduler = mock.MagicMock()
        scheduler.is_scheduled.return_value = False
        scheduler.add_job.side_effect = Exception('error')
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        result = job.schedule()
        self.assertIsNone(result)
        self.assertEqual(job.job_doc_status, 'completed')

    def test_job_unschedule(self):
        scheduler = mock.MagicMock()
        scheduler.remove_job.side_effect = Exception('error')
        job = scheduler_job.Job(scheduler, None, self.jobdoc)
        result = job.unschedule()
        self.assertIsNone(result)

    def test_job_terminate_kill(self):
        process = mock.MagicMock()
        self.job.process = process
        self.assertIsNone(self.job.terminate())
        self.assertIsNone(self.job.kill())
