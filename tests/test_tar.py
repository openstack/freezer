"""Freezer Tar related tests

Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

"""

from commons import *
from freezer.tar import (tar_restore, tar_backup,  get_tar_flag_from_algo)
from freezer import winutils

import os
import logging
import subprocess
import pytest


class TestTar:

    def test_tar_restore(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakesubprocess = FakeSubProcess5()
        fakesubprocesspopen = fakesubprocess.Popen()
        fakemultiprocessing = FakeMultiProcessing()
        fakepipe = fakemultiprocessing.Pipe()
        fakeos = Os()

        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(os, 'remove', fakeos.remove)
        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocesspopen)
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        pytest.raises(SystemExit, tar_restore, "", "",  fakepipe)

        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()
        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)
        assert tar_restore("", "", fakepipe) is None

        # expected_tar_cmd = 'gzip -dc | tar -xf - --unlink-first --ignore-zeros'
        monkeypatch.setattr(winutils, 'is_windows', ReturnBool.return_true)
        fake_os = Os()
        monkeypatch.setattr(os, 'chdir', fake_os.chdir)
        assert tar_restore("", "", fakepipe) is None

        monkeypatch.setattr(os, 'chdir', fake_os.chdir2)
        pytest.raises(Exception, tar_restore, backup_opt, "", fakepipe)

    def test_tar_backup(self, monkeypatch):

        fakelogging = FakeLogging()
        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()
        fakemultiprocessing = FakeMultiProcessing()
        fakebackup_queue = fakemultiprocessing.Queue()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert tar_backup(".", 100, 'tar_command', fakebackup_queue) is not False

    def test_tar_restore_args_valid(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        fakeos = Os()
        monkeypatch.setattr(os.path, 'exists', fakeos.exists)

        backup_opt.dry_run = True

        fakeos1 = Os1()
        monkeypatch.setattr(os.path, 'exists', fakeos1.exists)
        backup_opt.dry_run = False

    def test_get_tar_flag_from_algo(self):
        assert get_tar_flag_from_algo('gzip') == '-z'
        assert get_tar_flag_from_algo('bzip2') == '-j'
        assert get_tar_flag_from_algo('xz') == '-J'
