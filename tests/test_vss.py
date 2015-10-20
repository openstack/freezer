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

from commons import (FakeDisableFileSystemRedirection, FakeSubProcess,
    FakeSubProcess3, FakeSubProcess6)
from freezer import vss
from freezer import winutils
import subprocess


class TestVss:

    def test_vss_create_shadow_copy(self, monkeypatch):
        fake_disable_redirection = FakeDisableFileSystemRedirection()
        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        monkeypatch.setattr(
            winutils.DisableFileSystemRedirection, '__enter__',
            fake_disable_redirection.__enter__)
        monkeypatch.setattr(
            winutils.DisableFileSystemRedirection, '__exit__',
            fake_disable_redirection.__exit__)

        assert vss.vss_create_shadow_copy('C:\\') is not False

        fakesubprocess = FakeSubProcess3()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        pytest.raises(Exception, vss.vss_create_shadow_copy('C:\\'))

    def test_vss_delete_shadow_copy(self, monkeypatch):
        fake_disable_redirection = FakeDisableFileSystemRedirection()
        monkeypatch.setattr(
            winutils.DisableFileSystemRedirection, '__enter__',
            fake_disable_redirection.__enter__)
        monkeypatch.setattr(
            winutils.DisableFileSystemRedirection, '__exit__',
            fake_disable_redirection.__exit__)

        fakesubprocess = FakeSubProcess6()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(subprocess, 'Popen', fakesubprocesspopen)
        monkeypatch.setattr(subprocess.Popen, 'communicate',
                            fakesubprocesspopen.communicate)

        pytest.raises(Exception, vss.vss_delete_shadow_copy('', ''))

        fakesubprocess = FakeSubProcess3()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        pytest.raises(Exception, vss.vss_delete_shadow_copy('shadow_id',
                                                            'C:\\'))

        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        assert vss.vss_delete_shadow_copy('shadow_id', 'C:\\') is True
