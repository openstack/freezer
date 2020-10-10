"""Freezer admin.py related tests

(c) Copyright 2018 ZTE Corporation.
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

from freezer.openstack import admin
from freezer.tests import commons


class TestAdmin(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestAdmin, self).setUp()
        self.backup_opt = commons.BackupOpt1()
        self.admin_os = admin.AdminOs(self.backup_opt.client_manager)
        self.client_manager = self.backup_opt.client_manager

    def test_del_cinderbackup_and_dependend_incremental(self):
        self.admin_os.del_cinderbackup_and_dependend_incremental(1)
        try:
            self.admin_os.del_cinderbackup_and_dependend_incremental(1023)
        except Exception as e:
            msg = "Delete backup 1023 failed, the status of backup is error."
            self.assertEqual(msg, str(e))

        try:
            self.admin_os.del_cinderbackup_and_dependend_incremental(1024)
        except Exception as e:
            msg = "Delete backup 1024 failed due to timeout over 120s," \
                  " the status of backup is deleting."
            self.assertEqual(msg, str(e))

    def test_del_off_limit_fullbackup_keep(self):
        self.admin_os.del_off_limit_fullbackup('2', 1)

    def test_del_off_limit_fullbackup_keep_two(self):
        self.admin_os.del_off_limit_fullbackup('2', 2)

    def test_remove_cinderbackup_older_than(self):
        self.admin_os.remove_cinderbackup_older_than(35, 1463896546.0)
        try:
            self.admin_os.remove_cinderbackup_older_than(1023, 1463896546.0)
        except Exception as e:
            msg = "Delete backup 1023 failed, the status of backup is error."
            self.assertEqual(msg, str(e))

        try:
            self.admin_os.remove_cinderbackup_older_than(1024, 1463896546.0)
        except Exception as e:
            msg = "Delete backup 1024 failed due to timeout over 120s," \
                  " the status of backup is deleting."
            self.assertEqual(msg, str(e))
