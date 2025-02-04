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

from freezer.scheduler.freezer_scheduler import FreezerScheduler
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
        self.scheduler = FreezerScheduler(
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
