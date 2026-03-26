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
            mock_conf.os_username = ''
            mock_conf.service_auth.os_username = 'service_user'
            freezer_scheduler.update_auth_options(mock_conf, opts)
            self.assertEqual('service_user', opts.os_username)

            # Case 2: CONF has value (CLI/Env), service_auth has value.
            # Should prefer CONF value, so opts is NOT updated
            # (client gets it from CONF directly via opts.opts)
            mock_conf.os_username = 'admin_user'
            mock_conf.service_auth.os_username = 'service_user'
            opts = mock.Mock(spec=[])
            freezer_scheduler.update_auth_options(mock_conf, opts)
            self.assertFalse(hasattr(opts, 'os_username'))
