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

import subprocess
import unittest

import mock
from mock import patch

from freezer.utils import exec_cmd


class TestExec(unittest.TestCase):
    def test_exec_cmd(self):
        cmd = "echo test > test.txt"
        popen = patch('freezer.utils.exec_cmd.subprocess.Popen')
        mock_popen = popen.start()
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.communicate = mock.Mock()
        mock_popen.return_value.communicate.return_value = ['some stderr']
        mock_popen.return_value.returncode = 0
        exec_cmd.execute(cmd)
        assert (mock_popen.call_count == 1)
        mock_popen.assert_called_with(['echo', 'test', '>', 'test.txt'],
                                      shell=False,
                                      stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE)
        popen.stop()

    def test__exec_cmd_with_pipe(self):
        cmd = "echo test|wc -l"
        popen = patch('freezer.utils.exec_cmd.subprocess.Popen')
        mock_popen = popen.start()
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.communicate = mock.Mock()
        mock_popen.return_value.communicate.return_value = ['some stderr']
        mock_popen.return_value.returncode = 0
        exec_cmd.execute(cmd)
        assert (mock_popen.call_count == 2)
        popen.stop()
