"""Freezer restore.py related tests

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
from freezer.restore import (
    restore_fs, restore_fs_sort_obj)
import freezer
import logging
import pytest
import swiftclient


class TestRestore:

    def test_restore_fs(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(
            freezer.restore, 'restore_fs_sort_obj', fake_restore_fs_sort_obj)

        fakeclient = FakeSwiftClient()
        fakeconnector = fakeclient.client
        monkeypatch.setattr(swiftclient, 'client', fakeconnector)

        assert restore_fs(backup_opt) is None

        backup_opt = BackupOpt1()
        backup_opt.container = None
        pytest.raises(Exception, restore_fs, backup_opt)

        backup_opt = BackupOpt1()
        backup_opt.restore_from_date = None
        assert restore_fs(backup_opt) is None

        monkeypatch.setattr(
            freezer.utils, 'get_match_backup', fake_get_match_backup)
        backup_opt = BackupOpt1()
        backup_opt.remote_obj_list = [{'name': 'tsdfgsdfs',
            'last_modified': 'testdate'}]
        backup_opt.remote_match_backup = []
        pytest.raises(ValueError, restore_fs, backup_opt)


    def test_restore_fs_sort_obj(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert restore_fs_sort_obj(backup_opt) is None

        backup_opt = BackupOpt1()
        backup_opt.backup_name = 'abcdtest'
        pytest.raises(Exception, restore_fs_sort_obj, backup_opt)
