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

from mock import patch, Mock
import unittest

from freezer.tests.commons import *
from freezer import job as jobs


class TestJob(unittest.TestCase):
    def test_execute(self):
        opt = BackupOpt1()
        job = jobs.InfoJob(opt, opt.storage)
        assert job.execute() is None


class TestInfoJob(TestJob):

    def test_execute_nothing_to_do(self):
        backup_opt = BackupOpt1()
        job = jobs.InfoJob(backup_opt, backup_opt.storage)
        job.execute()

    def test_execute_list_containers(self):
        backup_opt = BackupOpt1()
        job = jobs.InfoJob(backup_opt, backup_opt.storage)
        job.execute()


class TestBackupJob(TestJob):

    def test_execute_backup_fs_no_incremental_and_backup_level_raise(self):
        backup_opt = BackupOpt1()
        backup_opt.mode = 'default'
        backup_opt.no_incremental = True
        job = jobs.BackupJob(backup_opt, backup_opt.storage)
        self.assertRaises(Exception, job.execute)

    def test_execute_raise(self):
        backup_opt = BackupOpt1()
        backup_opt.no_incremental = False
        backup_opt.mode = None
        job = jobs.BackupJob(backup_opt, backup_opt.storage)
        self.assertRaises(ValueError, job.execute)


class TestAdminJob(TestJob):
    def test_execute(self):
        backup_opt = BackupOpt1()
        jobs.AdminJob(backup_opt, backup_opt.storage).execute()


class TestExecJob(TestJob):

    def setUp(self):
        #init mock_popen
        self.popen = patch('freezer.utils.exec_cmd.subprocess.Popen')
        self.mock_popen = self.popen.start()
        self.mock_popen.return_value = Mock()
        self.mock_popen.return_value.communicate = Mock()
        self.mock_popen.return_value.communicate.return_value = ['some stderr']

    def tearDown(self):
        self.popen.stop()

    def test_execute_nothing_to_do(self):
        backup_opt = BackupOpt1()
        jobs.ExecJob(backup_opt, backup_opt.storage).execute()

    def test_execute_script(self):
        self.mock_popen.return_value.returncode = 0
        backup_opt = BackupOpt1()
        backup_opt.command='echo test'
        jobs.ExecJob(backup_opt, backup_opt.storage).execute()

    def test_execute_raise(self):
        self.popen=patch('freezer.utils.exec_cmd.subprocess.Popen')
        self.mock_popen=self.popen.start()
        self.mock_popen.return_value.returncode = 1
        backup_opt = BackupOpt1()
        backup_opt.command = 'echo test'
        job = jobs.ExecJob(backup_opt, backup_opt.storage)
        self.assertRaises(Exception, job.execute)
