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
import unittest

import mock

from freezer.tests import commons
from freezer.utils import winutils


class TestWinutils(unittest.TestCase):

    def mock_process(self, process):
        fakesubprocesspopen = process.Popen()
        mock.patch('subprocess.Popen.communicate',
                   new_callable=fakesubprocesspopen.communicate).start()
        mock.patch('subprocess.Popen', new_callable=fakesubprocesspopen)\
            .start()

    def mock_winutils(self):
        fake_disable_redirection = commons.FakeDisableFileSystemRedirection()
        mock.patch('winutils.DisableFileSystemRedirection.__enter__',
                   new_callable=fake_disable_redirection.__enter__)
        mock.patch('winutils.DisableFileSystemRedirection.__exit__',
                   new_callable=fake_disable_redirection.__exit__)

    def test_is_windows(self):
        fake_os = commons.Os()
        os.name = fake_os
        assert winutils.is_windows() is False

    def test_use_shadow(self):
        test_volume = 'C:'
        test_volume2 = 'C:\\'
        path = 'C:\\Users\\Test'
        expected = 'C:\\freezer_shadowcopy\\Users\\Test'
        assert winutils.use_shadow(path, test_volume2) == expected

        # test if the volume format is incorrect
        self.assertRaises(Exception,
                          winutils.use_shadow(path, test_volume))  # noqa

    # def test_start_sql_server(self):
    #     backup_opt = BackupOpt1()
    #     self.mock_process(FakeSubProcess())
    #     self.mock_winutils()
    #
    #     assert winutils.start_sql_server(
    #         backup_opt.sql_server_instance) is not False
    #
    #     self.mock_process(FakeSubProcess3())
    #     self.assertRaises(
    #         Exception,
    #         winutils.start_sql_server(backup_opt.sql_server_instance))
    #
    # def test_stop_sql_server(self):
    #     backup_opt = BackupOpt1()
    #     self.mock_process(FakeSubProcess())
    #     self.mock_winutils()
    #
    #     assert winutils.start_sql_server(
    #         backup_opt.sql_server_instance) is not False
    #
    #     self.mock_process(FakeSubProcess3())
    #
    #     self.assertRaises(Exception, winutils.stop_sql_server(
    #         backup_opt.sql_server_instance))
