"""
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

========================================================================
"""

from commons import *
from freezer.lvm import (
    lvm_eval, lvm_snap_remove, lvm_snap)
from freezer import utils
import __builtin__
import pytest
import StringIO
import logging


class TestLvm:

    def test_lvm_eval(self):

        backup_opt = BackupOpt1()
        assert lvm_eval(backup_opt) is True

        backup_opt.__dict__['lvm_dirmount'] = None
        assert lvm_eval(backup_opt) is False

    def test_lvm_snap_remove(self, monkeypatch):

        fakeopen = FakeOpen()
        fakelogging = FakeLogging()
        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()

        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            subprocess, 'Popen', fakesubprocesspopen)
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        backup_opt = BackupOpt1()
        pytest.raises(Exception, lvm_snap_remove, backup_opt)

        backup_opt.__dict__['lvm_volgroup'] = False
        assert lvm_snap_remove(backup_opt) is True

        backup_opt = BackupOpt1()
        monkeypatch.setattr(__builtin__, 'open', fakeopen.fopen)
        pytest.raises(Exception, lvm_snap_remove, backup_opt)

        fakere = FakeRe2()
        monkeypatch.setattr(re, 'search', fakere.search)

        assert lvm_snap_remove(backup_opt) is True

    def test_lvm_snap(self, monkeypatch):

        backup_opt = BackupOpt1()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        pytest.raises(Exception, lvm_snap, backup_opt)


        backup_opt = BackupOpt1()
        fakeos = Os()
        fakesubprocess = FakeSubProcess()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        pytest.raises(Exception, lvm_snap, backup_opt)

        get_vol_fs_type = Fake_get_vol_fs_type()
        backup_opt = BackupOpt1()
        fakeos = Os()
        fakesubprocess = FakeSubProcess2()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        monkeypatch.setattr(utils, 'get_vol_fs_type', get_vol_fs_type.get_vol_fs_type1)
        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        assert lvm_snap(backup_opt) is True

        get_vol_fs_type = Fake_get_vol_fs_type()
        backup_opt = BackupOpt1()
        fakeos = Os()
        fakesubprocess = FakeSubProcess3()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        monkeypatch.setattr(utils, 'get_vol_fs_type', get_vol_fs_type.get_vol_fs_type1)
        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        pytest.raises(Exception, lvm_snap, backup_opt)

        get_vol_fs_type = Fake_get_vol_fs_type()
        backup_opt = BackupOpt1()
        fakeos = Os()
        fakesubprocess = FakeSubProcess1()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        monkeypatch.setattr(utils, 'get_vol_fs_type', get_vol_fs_type.get_vol_fs_type1)
        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        pytest.raises(Exception, lvm_snap, backup_opt)

        get_vol_fs_type = Fake_get_vol_fs_type()
        backup_opt = BackupOpt1()
        fakeos = Os()
        fakesubprocess = FakeSubProcess4()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        monkeypatch.setattr(utils, 'get_vol_fs_type', get_vol_fs_type.get_vol_fs_type1)
        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        assert lvm_snap(backup_opt) is True

        get_vol_fs_type = Fake_get_vol_fs_type()
        backup_opt = BackupOpt1()
        backup_opt.lvm_dirmount = None
        fakeos = Os()
        fakesubprocess = FakeSubProcess4()
        backup_opt.lvm_snapsize = False
        backup_opt.lvm_snapname = False
        monkeypatch.setattr(os, 'path', fakeos)
        monkeypatch.setattr(subprocess, 'Popen', fakesubprocess.Popen)
        monkeypatch.setattr(utils, 'get_vol_fs_type', get_vol_fs_type.get_vol_fs_type1)
        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        assert lvm_snap(backup_opt) is True
