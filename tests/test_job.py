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
from freezer import (
    swift, restore, utils, backup)

from freezer.job import Job, InfoJob, AdminJob, BackupJob, RestoreJob, create_job
import logging

import pytest


class TestJob:

    def do_monkeypatch(self, monkeypatch):
        fakelogging = FakeLogging()
        self.fakeswift = fakeswift = FakeSwift()
        self.fakeutils = FakeUtils()
        self.fakebackup = FakeBackup()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(swift, 'get_client', fakeswift.fake_get_client)
        monkeypatch.setattr(swift, 'get_containers_list', fakeswift.fake_get_containers_list1)

    def test_execute(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        job = Job({})
        assert job.execute() is None


class TestInfoJob(TestJob):

    def test_execute_nothing_to_do(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        job = InfoJob(backup_opt)
        assert job.execute() is False

    def test_execute_list_container(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.list_container = True
        job = InfoJob(backup_opt)
        assert job.execute() is True

    def test_execute_list_objects(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(swift, 'show_containers', self.fakeswift.fake_show_containers)
        monkeypatch.setattr(swift, 'show_objects', self.fakeswift.fake_show_objects)
        backup_opt = BackupOpt1()
        backup_opt.list_objects = True
        job = InfoJob(backup_opt)
        assert job.execute() is True

    def test_execute_container_not_exist(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.list_objects = True
        monkeypatch.setattr(swift, 'check_container_existance', self.fakeswift.fake_check_container_existance1)
        job = InfoJob(backup_opt)
        assert job.execute() is False


class TestBackupJob(TestJob):

    def test_execute_backup_fs_incremental(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(swift, 'check_container_existance', self.fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', self.fakeswift.fake_get_containers_list4)
        monkeypatch.setattr(utils, 'set_backup_level', self.fakeutils.fake_set_backup_level)
        monkeypatch.setattr(backup, 'backup_mode_fs', self.fakebackup.fake_backup_mode_fs)
        monkeypatch.setattr(swift, 'get_container_content', self.fakeswift.fake_get_container_content)
        backup_opt = BackupOpt1()
        backup_opt.mode = 'fs'
        backup_opt.no_incremental = False
        job = BackupJob(backup_opt)
        assert job.execute() is None

    def test_execute_backup_fs_no_incremental_and_backup_level_raise(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.mode = 'fs'
        backup_opt.no_incremental = True
        job = BackupJob(backup_opt)
        pytest.raises(Exception, job.execute)

    def test_execute_backup_mongo(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(utils, 'set_backup_level', self.fakeutils.fake_set_backup_level)
        monkeypatch.setattr(swift, 'get_container_content', self.fakeswift.fake_get_container_content)
        monkeypatch.setattr(backup, 'backup_mode_mongo', self.fakebackup.fake_backup_mode_mongo)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = 'mongo'
        job = BackupJob(backup_opt)
        assert job.execute() is None

    def test_execute_backup_mysql(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(utils, 'set_backup_level', self.fakeutils.fake_set_backup_level)
        monkeypatch.setattr(swift, 'get_container_content', self.fakeswift.fake_get_container_content)
        monkeypatch.setattr(backup, 'backup_mode_mysql', self.fakebackup.fake_backup_mode_mysql)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = 'mysql'
        job = BackupJob(backup_opt)
        assert job.execute() is None

    def test_execute_raise(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(utils, 'set_backup_level', self.fakeutils.fake_set_backup_level)
        monkeypatch.setattr(swift, 'get_container_content', self.fakeswift.fake_get_container_content)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = None
        job = BackupJob(backup_opt)
        pytest.raises(ValueError, job.execute)


class TestRestoreJob(TestJob):

    def test_execute_raise(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(swift, 'check_container_existance', self.fakeswift.fake_check_container_existance1)
        monkeypatch.setattr(swift, 'get_containers_list', self.fakeswift.fake_get_containers_list3)
        backup_opt = BackupOpt1()
        job = RestoreJob(backup_opt)
        #assert job.execute() is None
        pytest.raises(Exception, job.execute)


    def test_execute(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        fakerestore = FakeRestore()
        monkeypatch.setattr(swift, 'check_container_existance', self.fakeswift.fake_check_container_existance)
        monkeypatch.setattr(swift, 'get_containers_list', self.fakeswift.fake_get_containers_list3)
        monkeypatch.setattr(restore, 'restore_fs', fakerestore.fake_restore_fs)
        monkeypatch.setattr(swift, 'get_container_content', self.fakeswift.fake_get_container_content)
        backup_opt = BackupOpt1()
        job = RestoreJob(backup_opt)
        assert job.execute() is None


class TestAdminJob(TestJob):
    def test_execute(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(swift, 'remove_obj_older_than', self.fakeswift.remove_obj_older_than)
        backup_opt = BackupOpt1()
        job = AdminJob(backup_opt)
        assert job.execute() is None


def test_create_job():
    backup_opt = BackupOpt1()
    backup_opt.action = None
    pytest.raises(Exception, create_job, backup_opt)

    backup_opt.action = 'backup'
    job = create_job(backup_opt)
    assert isinstance(job, BackupJob)

    backup_opt.action = 'restore'
    job = create_job(backup_opt)
    assert isinstance(job, RestoreJob)

    backup_opt.action = 'info'
    job = create_job(backup_opt)
    assert isinstance(job, InfoJob)

    backup_opt.action = 'admin'
    job = create_job(backup_opt)
    assert isinstance(job, AdminJob)

