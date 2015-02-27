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
from freezer.tar import (tar_restore, tar_incremental, tar_backup,
    gen_tar_command, tar_restore_args_valid)

import os
import logging
import subprocess
import pytest
import time


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
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        pytest.raises(SystemExit, tar_restore, backup_opt, fakepipe)

        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()
        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)
        assert tar_restore(backup_opt, fakepipe) is None


    def test_tar_incremental(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        (tar_cmd, curr_tar_meta,
            remote_manifest_meta) = True, True, {}
        (val1, val2, val3) =  tar_incremental(
            tar_cmd, backup_opt, curr_tar_meta,
            remote_manifest_meta)
        assert val1 is not False
        assert val2 is not False
        assert val3 is not False

        (tar_cmd, curr_tar_meta,
            remote_manifest_meta) = False, True, {}
        pytest.raises(Exception, tar_incremental, tar_cmd, backup_opt, curr_tar_meta, remote_manifest_meta)

    def test_gen_tar_command(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        (meta_data_backup_file, remote_manifest_meta) = True, {}
        time_stamp = int(time.time())
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        (val1, val2, val3) = gen_tar_command(backup_opt, meta_data_backup_file, time_stamp,
        remote_manifest_meta)
        assert val1 is not False
        assert val2 is not False
        assert val3 is not False

        backup_opt.__dict__['dereference_symlink'] = 'soft'
        (val1, val2, val3) = gen_tar_command(backup_opt, meta_data_backup_file, time_stamp,
        remote_manifest_meta)
        assert val1 is not False
        assert val2 is not False
        assert val3 is not False

        backup_opt.__dict__['dereference_symlink'] = 'hard'
        (val1, val2, val3) = gen_tar_command(backup_opt, meta_data_backup_file, time_stamp,
        remote_manifest_meta)
        assert val1 is not False
        assert val2 is not False
        assert val3 is not False

        backup_opt.__dict__['dereference_symlink'] = 'all'
        (val1, val2, val3) = gen_tar_command(backup_opt, meta_data_backup_file, time_stamp,
        remote_manifest_meta)
        assert val1 is not False
        assert val2 is not False
        assert val3 is not False

        backup_opt.__dict__['src_file'] = ''
        pytest.raises(Exception, gen_tar_command,
                      backup_opt, meta_data_backup_file, time_stamp,
                      remote_manifest_meta)

    def test_tar_backup(self, monkeypatch):

        backup_opt = BackupOpt1()
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

        backup_opt.__dict__['max_seg_size'] = 1
        assert tar_backup(backup_opt, 'tar_command', fakebackup_queue) is not False

    def test_tar_restore_args_valid(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        fakeos = Os()
        monkeypatch.setattr(os.path, 'exists', fakeos.exists)
        assert tar_restore_args_valid(backup_opt) is True

        backup_opt.dry_run = True
        assert tar_restore_args_valid(backup_opt) is True

        fakeos1 = Os1()
        monkeypatch.setattr(os.path, 'exists', fakeos1.exists)
        backup_opt.dry_run = False
        assert tar_restore_args_valid(backup_opt) is False
