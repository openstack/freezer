"""Freezer main.py related tests

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
from freezer.main import freezer_main
from freezer import (
    swift, restore, utils, backup)

import logging
import pytest


class TestMain:

    def test_freezer_main(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakeswift = FakeSwift()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        monkeypatch.setattr(swift, 'get_client', fakeswift.fake_get_client)
        monkeypatch.setattr(swift, 'show_containers', fakeswift.fake_show_containers)
        monkeypatch.setattr(swift, 'show_objects', fakeswift.fake_show_objects)

        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list1)
        assert freezer_main(backup_opt) is True

        fakeswift = FakeSwift()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list)
        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is True

        fakeswift = FakeSwift()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list1)
        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is False

        fakeswift = FakeSwift()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list2)
        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is False

        fakeswift = FakeSwift()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list3)
        backup_opt = BackupOpt1()
        backup_opt.action = 'restore'
        pytest.raises(Exception, freezer_main, backup_opt)

        fakeswift = FakeSwift()
        fakerestore = FakeRestore()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list3)
        monkeypatch.setattr(restore, 'restore_fs', fakerestore.fake_restore_fs)
        monkeypatch.setattr(swift, 'get_container_content', fakeswift.fake_get_container_content)
        backup_opt = BackupOpt1()
        backup_opt.action = 'restore'
        assert freezer_main(backup_opt) is None

        fakeswift = FakeSwift()
        fakeutils = FakeUtils()
        fakebackup = FakeBackup()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list4)
        monkeypatch.setattr(utils, 'set_backup_level', fakeutils.fake_set_backup_level_fs)
        monkeypatch.setattr(backup, 'backup_mode_fs', fakebackup.fake_backup_mode_fs)

        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is None

        fakeswift = FakeSwift()
        fakeutils = FakeUtils()
        fakebackup = FakeBackup()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list4)
        monkeypatch.setattr(utils, 'set_backup_level', fakeutils.fake_set_backup_level_mongo)
        monkeypatch.setattr(backup, 'backup_mode_mongo', fakebackup.fake_backup_mode_mongo)

        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is None

        fakeswift = FakeSwift()
        fakeutils = FakeUtils()
        fakebackup = FakeBackup()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list4)
        monkeypatch.setattr(utils, 'set_backup_level', fakeutils.fake_set_backup_level_mysql)
        monkeypatch.setattr(backup, 'backup_mode_mysql', fakebackup.fake_backup_mode_mysql)

        backup_opt = BackupOpt1()
        assert freezer_main(backup_opt) is None

        fakeswift = FakeSwift()
        fakeutils = FakeUtils()
        monkeypatch.setattr(swift, 'check_container_existance', fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list4)
        monkeypatch.setattr(utils, 'set_backup_level', fakeutils.fake_set_backup_level_none)

        backup_opt = BackupOpt1()
        pytest.raises(ValueError, freezer_main, backup_opt)
