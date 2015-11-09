"""Freezer main.py related tests

(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from commons import *
from freezer import (restore, backup, exec_cmd)
from freezer.job import (
    Job, InfoJob, AdminJob, BackupJob, RestoreJob, ExecJob, create_job)
from freezer import (restore, backup)

from freezer.job import Job, InfoJob, AdminJob, BackupJob, RestoreJob, create_job
import logging
from mock import patch, Mock
import unittest


class TestJob:

    def do_monkeypatch(self, monkeypatch):
        self.fakebackup = FakeBackup()

    def test_execute(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        job = Job(BackupOpt1())
        assert job.execute() is None


class TestInfoJob(TestJob):

    def test_execute_nothing_to_do(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        job = InfoJob(backup_opt)
        job.execute()

    def test_execute_list_containers(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.list_containers = True
        job = InfoJob(backup_opt)
        job.execute()


class TestBackupJob(TestJob):

    def test_execute_backup_fs_no_incremental_and_backup_level_raise(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.mode = 'fs'
        backup_opt.no_incremental = True
        job = BackupJob(backup_opt)
        pytest.raises(Exception, job.execute)

    def test_execute_backup_mongo(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(backup, 'backup_mode_mongo', self.fakebackup.fake_backup_mode_mongo)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = 'mongo'
        job = BackupJob(backup_opt)
        assert job.execute() is None

    def test_execute_backup_mysql(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        monkeypatch.setattr(backup, 'backup_mode_mysql', self.fakebackup.fake_backup_mode_mysql)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = 'mysql'
        job = BackupJob(backup_opt)
        assert job.execute() is None

    def test_execute_raise(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = None
        job = BackupJob(backup_opt)
        pytest.raises(ValueError, job.execute)


class TestAdminJob(TestJob):
    def test_execute(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        job = AdminJob(backup_opt)
        assert job.execute() is None


class TestExecJob(TestJob):

    def setUp(self):
        #init mock_popen
        self.popen=patch('freezer.exec_cmd.subprocess.Popen')
        self.mock_popen=self.popen.start()
        self.mock_popen.return_value = Mock()
        self.mock_popen.return_value.communicate = Mock()
        self.mock_popen.return_value.communicate.return_value = ['some stderr']

    def tearDown(self):
        self.popen.stop()

    def test_execute_nothing_to_do(self, monkeypatch):
        self.do_monkeypatch(monkeypatch)
        backup_opt = BackupOpt1()
        job = ExecJob(backup_opt)
        assert job.execute() is False

    def test_execute_script(self, monkeypatch):
        self.setUp()
        self.do_monkeypatch(monkeypatch)
        self.mock_popen.return_value.returncode = 0
        backup_opt = BackupOpt1()
        backup_opt.command='echo test'
        job = ExecJob(backup_opt)
        assert job.execute() is True
        self.tearDown()

    def test_execute_raise(self, monkeypatch):
        self.setUp()
        self.do_monkeypatch(monkeypatch)
        popen=patch('freezer.exec_cmd.subprocess.Popen')
        self.mock_popen.return_value.returncode = 1
        backup_opt = BackupOpt1()
        backup_opt.command='echo test'
        job = ExecJob(backup_opt)
        pytest.raises(Exception, job.execute)
        self.tearDown()


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

    backup_opt.action = 'exec'
    job = create_job(backup_opt)
    assert isinstance(job, ExecJob)
