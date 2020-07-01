"""Freezer backup.py related tests

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

from freezer.openstack import backup
from freezer.tests import commons


class TestBackup(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestBackup, self).setUp()
        self.backup_opt = commons.BackupOpt1()
        self.bakup_os = backup.BackupOs(self.backup_opt.client_manager,
                                        self.backup_opt.container,
                                        self.backup_opt.storage)
        self.client_manager = self.backup_opt.client_manager
        self.storage = self.backup_opt.storage

    def test_backup_cinder_by_glance(self):
        self.bakup_os.backup_cinder_by_glance(35)

    def test_backup_cinder_with_incremental(self):
        self.bakup_os.backup_cinder(35, incremental=True)

    def test_backup_cinder_without_incremental(self):
        self.bakup_os.backup_cinder(35, incremental=False)
