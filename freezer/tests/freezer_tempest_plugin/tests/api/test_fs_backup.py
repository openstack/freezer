# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import shutil

from oslo_utils import uuidutils
from tempest.lib import decorators

from freezer.tests.freezer_tempest_plugin.tests.api import base


class TestFreezerFSBackup(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerFSBackup, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestFreezerFSBackup, self).setUp()

        test_id = uuidutils.generate_uuid(dashed=False)

        self.backup_source_dir = (
            "/tmp/freezer-test-backup-source/" + test_id
        )

        self.backup_source_sub_dir = self.backup_source_dir + "/subdir"

        self.restore_target_dir = (
            "/tmp/freezer-test-backup-restore/" + test_id
        )

        self.backup_local_storage_dir = (
            "/tmp/freezer-test-backup-local-storage/" + test_id
        )

        self.freezer_backup_name = 'freezer-test-backup-fs-0'

        shutil.rmtree(self.backup_source_dir, True)
        os.makedirs(self.backup_source_dir)
        open(self.backup_source_dir + "/a", 'w').close()
        open(self.backup_source_dir + "/b", 'w').close()
        open(self.backup_source_dir + "/c", 'w').close()

        os.makedirs(self.backup_source_sub_dir)
        open(self.backup_source_sub_dir + "/x", 'w').close()
        open(self.backup_source_sub_dir + "/y", 'w').close()
        open(self.backup_source_sub_dir + "/z", 'w').close()

        shutil.rmtree(self.restore_target_dir, True)
        os.makedirs(self.restore_target_dir)

        shutil.rmtree(self.backup_local_storage_dir, True)
        os.makedirs(self.backup_local_storage_dir)

        self.environ = super(TestFreezerFSBackup, self).get_environ()

    def tearDown(self):
        super(TestFreezerFSBackup, self).tearDown()
        shutil.rmtree(self.backup_source_dir, True)
        shutil.rmtree(self.restore_target_dir, True)
        shutil.rmtree(self.backup_local_storage_dir)

    @decorators.attr(type="gate")
    def test_freezer_fs_backup(self):
        backup_args = ['freezer-agent',
                       '--path-to-backup',
                       self.backup_source_dir,
                       '--container',
                       self.backup_local_storage_dir,
                       '--backup-name',
                       self.freezer_backup_name,
                       '--storage',
                       'local']

        self.run_subprocess(backup_args, "Test backup to local storage.")

        restore_args = ['freezer-agent',
                        '--action',
                        'restore',
                        '--restore-abs-path',
                        self.restore_target_dir,
                        '--container',
                        self.backup_local_storage_dir,
                        '--backup-name',
                        self.freezer_backup_name,
                        '--storage',
                        'local']

        self.run_subprocess(restore_args, "Test restore from local storage.")

        diff_args = ['diff',
                     '-r',
                     '-q',
                     self.backup_source_dir,
                     self.restore_target_dir]

        self.run_subprocess(diff_args,
                            "Test backup restore from local storage "
                            "diff.")
