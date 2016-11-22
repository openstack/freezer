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

import unittest

import mock

from freezer.tests.commons import FakeDisableFileSystemRedirection


class TestVss(unittest.TestCase):
    def mock_process(self, process):
        fakesubprocesspopen = process.Popen()
        mock.patch('subprocess.Popen.communicate',
                   new_callable=fakesubprocesspopen.communicate).start()
        mock.patch('subprocess.Popen',
                   new_callable=fakesubprocesspopen.start())

    def mock_winutils(self):
        fake_disable_redirection = FakeDisableFileSystemRedirection()
        mock.patch('winutils.DisableFileSystemRedirection.__enter__',
                   new_callable=fake_disable_redirection.__enter__,
                   )
        mock.patch('winutils.DisableFileSystemRedirection.__exit__',
                   new_callable=fake_disable_redirection.__exit__,
                   )

    # def test_vss_create_shadow_copy(self):
    #     self.mock_process(FakeSubProcess())
    #     self.mock_winutils()
    #     assert vss.vss_create_shadow_copy('C:\\') is not False
    #     self.mock_process(FakeSubProcess3())
    #     self.assertRaises(Exception, vss.vss_create_shadow_copy('C:\\'))
    #
    # def test_vss_delete_shadow_copy(self):
    #     self.mock_winutils()
    #     self.mock_process(FakeSubProcess6())
    #     self.assertRaises(Exception, vss.vss_delete_shadow_copy('', ''))
    #     self.mock_process(FakeSubProcess3())
    #     self.assertRaises(Exception, vss.vss_delete_shadow_copy('shadow_id',
    #                                                             'C:\\'))
    #     self.mock_process(FakeSubProcess())
    #     assert vss.vss_delete_shadow_copy('shadow_id', 'C:\\') is True
