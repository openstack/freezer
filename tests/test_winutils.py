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

from freezer.winutils import is_windows
from freezer.winutils import use_shadow
from freezer.winutils import clean_tar_command
from freezer.winutils import add_gzip_to_command
from freezer.winutils import DisableFileSystemRedirection
from freezer import winutils
from commons import *
import logging


class TestWinutils:

    def test_is_windows(self, monkeypatch):
        fake_os = Os()
        monkeypatch.setattr(os, 'name', fake_os)
        assert is_windows() is False

    def test_use_shadow(self):
        test_volume = 'C:'
        test_volume2 = 'C:\\'
        path = 'C:\\Users\\Test'
        expected = 'C:\\freezer_shadowcopy\\Users\\Test'
        assert use_shadow(path, test_volume2) == expected

        # test if the volume format is incorrect
        pytest.raises(Exception, use_shadow(path, test_volume))

    def test_clean_tar_command(self):
        test_tar_command = 'tar --create -z --warning=none ' \
                           '--no-check-device --one-file-system ' \
                           '--preserve-permissions --same-owner --seek ' \
                           '--ignore-failed-read '
        expected = 'tar --create    --one-file-system --preserve-permissions ' \
                   '--same-owner  --ignore-failed-read '

        assert clean_tar_command(test_tar_command) == expected

    def test_add_gzip_to_command(self):
        test_command = 'tar --create    --one-file-system ' \
                       '--preserve-permissions --same-owner ' \
                       '--ignore-failed-read '
        expected = 'tar --create    --one-file-system ' \
                   '--preserve-permissions --same-owner ' \
                   '--ignore-failed-read  | gzip -7'

        assert add_gzip_to_command(test_command) == expected

    def test_DisableFileSystemRedirection(self, monkeypatch):
        fake_disable_redirection = DisableFileSystemRedirection()
        fake_disable_redirection.success = True
        assert fake_disable_redirection._revert == ''
        assert fake_disable_redirection._disable == ''

        pytest.raises(Exception, fake_disable_redirection.__enter__)
        pytest.raises(Exception, fake_disable_redirection.__exit__)

    def test_start_sql_server(self, monkeypatch):
        fake_disable_redirection = FakeDisableFileSystemRedirection()
        backup_opt = BackupOpt1()
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

        assert winutils.start_sql_server(backup_opt) is not False

        fakesubprocess = FakeSubProcess3()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        pytest.raises(
            Exception,
            winutils.start_sql_server(backup_opt.sql_server_instance))

    def test_stop_sql_server(self, monkeypatch):
        fake_disable_redirection = FakeDisableFileSystemRedirection()
        backup_opt = BackupOpt1()
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

        assert winutils.start_sql_server(
            backup_opt.sql_server_instance) is not False

        fakesubprocess = FakeSubProcess3()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate',
            fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)

        pytest.raises(Exception, winutils.stop_sql_server(
            backup_opt.sql_server_instance))
