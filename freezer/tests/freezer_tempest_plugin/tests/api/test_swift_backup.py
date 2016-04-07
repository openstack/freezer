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

import datetime
import subprocess

from freezer.tests.freezer_tempest_plugin.tests.api import base
from tempest import test


class TestFreezerSwiftBackup(base.BaseFreezerTest):

    @test.attr(type="gate")
    def test_freezer_swift_backup(self):

        now_in_secs = datetime.datetime.now().strftime("%s")

        backup_source_dir = ("/tmp/freezer-test-backup-source/"
                             + now_in_secs)
        backup_source_sub_dir = backup_source_dir + "/subdir"

        restore_target_dir = (
            "/tmp/freezer-test-backup-restore/"
            + now_in_secs)

        freezer_container_name = 'freezer-test-container-0'
        freezer_backup_name = 'freezer-test-backup-0'

        shutil.rmtree(backup_source_dir, True)
        os.makedirs(backup_source_dir)
        open(backup_source_dir + "/a", 'w').close()
        open(backup_source_dir + "/b", 'w').close()
        open(backup_source_dir + "/c", 'w').close()

        os.makedirs(backup_source_sub_dir)
        open(backup_source_sub_dir + "/x", 'w').close()
        open(backup_source_sub_dir + "/y", 'w').close()
        open(backup_source_sub_dir + "/z", 'w').close()

        shutil.rmtree(restore_target_dir, True)
        os.makedirs(restore_target_dir)

        os.environ['OS_REGION_NAME'] = 'RegionOne'
        os.environ['OS_PASSWORD'] = 'secretadmin'
        os.environ['OS_IDENTITY_API_VERSION'] = '2.0'
        os.environ['OS_NO_CACHE'] = '1'
        os.environ['OS_USERNAME'] = 'demo'
        os.environ['OS_VOLUME_API_VERSION'] = '2'
        os.environ['OS_PROJECT_NAME'] = 'demo'
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['OS_TENANT_NAME'] = 'demo'
        os.environ['OS_TENANT_ID'] = ''
        os.environ['OS_AUTH_URL'] = 'http://localhost:5000/v2.0'
        # Mac OS X uses gtar located in /urs/local/bin
        os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']

        backup_args = ['freezer-agent',
                       '--path-to-backup',
                       backup_source_dir,
                       '--container',
                       freezer_container_name,
                       '--backup-name',
                       freezer_backup_name]

        output = subprocess.check_output(backup_args,
                                         stderr=subprocess.STDOUT,
                                         env=os.environ, shell=False)

        restore_args = ['freezer-agent',
                        '--action',
                        'restore',
                        '--restore-abs-path',
                        restore_target_dir,
                        '--container',
                        freezer_container_name,
                        '--backup-name',
                        freezer_backup_name,
                        '--storage',
                        'swift']

        output = subprocess.check_output(restore_args,
                                         stderr=subprocess.STDOUT,
                                         env=os.environ, shell=False)

        diff_args = ['diff',
                     '-r',
                     '-q',
                     backup_source_dir,
                     restore_target_dir]

        diff_rc = subprocess.call(diff_args,
                                  shell=False)

        self.assertEqual(0, diff_rc, "Test backup to swift and restore")

        shutil.rmtree(backup_source_dir, True)
        shutil.rmtree(restore_target_dir, True)
