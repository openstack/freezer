# (c) Copyright 2019 ZTE Corporation.
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
from unittest import mock
from unittest.mock import patch

from freezer.scheduler import utils

job_list = [{"job_id": "test"}]


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.client = mock.Mock()
        self.client.clients.create = mock.Mock(return_value='test')
        self.client.jobs.list = mock.Mock(return_value=job_list)
        self.client.client_id = "test"

    def test_do_register(self):
        ret = utils.do_register(self.client, args=None)
        self.assertEqual(0, ret)

    def test_find_config_files(self):
        temp = tempfile.NamedTemporaryFile('wb', delete=True,
                                           suffix='.conf')
        ret = utils.find_config_files(temp.name)
        self.assertEqual([temp.name], ret)
        temp.close()
        self.assertFalse(os.path.exists(temp.name))

    def test_find_config_files_path(self):
        temp = tempfile.NamedTemporaryFile('wb', delete=True,
                                           suffix='.conf')
        temp_path = os.path.dirname(temp.name)
        ret = utils.find_config_files(temp_path)
        self.assertEqual([temp.name], ret)
        temp.close()
        self.assertFalse(os.path.exists(temp.name))

    def test_get_jobs_from_disk(self):
        temp = tempfile.mkdtemp()
        file = '/'.join([temp, "test.conf"])
        data = b'{"job_id": "test"}'
        with open(file, 'wb') as f:
            f.write(data)
        ret = utils.get_jobs_from_disk(temp)
        self.assertEqual(job_list, ret)
        shutil.rmtree(temp)
        self.assertFalse(os.path.exists(file))

    def test_save_jobs_to_disk(self):
        job_doc_list = job_list
        tmpdir = tempfile.mkdtemp()
        utils.save_jobs_to_disk(job_doc_list, tmpdir)
        file = '/'.join([tmpdir, "job_test.conf"])
        self.assertTrue(os.path.exists(file))
        shutil.rmtree(tmpdir)

    def test_get_active_jobs_from_api(self):
        ret = utils.get_active_jobs_from_api(self.client)
        self.assertEqual(job_list, ret)

    @patch('psutil.Process')
    def test_terminate_subprocess(self, mock_process_constructor):
        mock_pro = mock_process_constructor.return_value
        seffect = mock.Mock(
            side_effect=Exception('Process 35 does not exists anymore'))
        mock_pro.raiseError.side_effect = seffect
        with self.assertRaises(Exception) as cm:  # noqa
            utils.terminate_subprocess(35, "test")
            the_exception = cm.exception
            self.assertIn('does not exists anymore',
                          str(the_exception))
