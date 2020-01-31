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
import tempfile
import unittest

from freezer.scheduler import scheduler_job

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
