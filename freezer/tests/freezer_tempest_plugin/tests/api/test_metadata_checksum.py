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
import json
import os
import subprocess

from freezer.tests.freezer_tempest_plugin.tests.api import base
from freezer.tests.integration.common import Temp_Tree
from tempest import test


class TestFreezerMetadataChecksum(base.BaseFreezerTest):

    def __init__(self, *args, **kwargs):
        super(TestFreezerMetadataChecksum, self).__init__(*args, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        super(TestFreezerMetadataChecksum, self).setUp()

        # create a source tree to backup with a few empty files
        # (files must be empty to avoid encoding errors with pure random data)
        self.source_tree = Temp_Tree()
        self.source_tree.add_random_data(size=0)

        self.storage_tree = Temp_Tree()
        self.dest_tree = Temp_Tree()

        self.freezer_backup_name = 'freezer-test-backup-checksum-0'

        self.metadata_out = os.path.join(
            self.storage_tree.path,
            self.freezer_backup_name + '.json')

        self.environ = super(TestFreezerMetadataChecksum, self).get_environ()

    def tearDown(self):
        super(TestFreezerMetadataChecksum, self).tearDown()

        self.source_tree.cleanup()
        self.dest_tree.cleanup()
        self.storage_tree.cleanup()

    @test.attr(type="gate")
    def test_freezer_fs_backup_valid_checksum(self):
        # perform a normal backup, but enable consistency checks and save the
        # metadata to disk
        backup_args = ['freezer-agent',
                       '--path-to-backup',
                       self.source_tree.path,
                       '--container',
                       self.storage_tree.path,
                       '--backup-name',
                       self.freezer_backup_name,
                       '--storage',
                       'local',
                       '--consistency_check',
                       '--metadata-out',
                       self.metadata_out]

        self.run_subprocess(backup_args, 'Test backup to local storage.')

        # load the stored metadata to retrieve the computed checksum
        with open(self.metadata_out) as f:
            metadata = json.load(f)
            self.assertIn('consistency_checksum', metadata,
                          'Checksum must exist in stored metadata.')

            checksum = metadata['consistency_checksum']
            restore_args = ['freezer-agent',
                            '--action',
                            'restore',
                            '--restore-abs-path',
                            self.dest_tree.path,
                            '--container',
                            self.storage_tree.path,
                            '--backup-name',
                            self.freezer_backup_name,
                            '--storage',
                            'local',
                            '--consistency_checksum',
                            checksum]

            self.run_subprocess(restore_args,
                                'Test restore from local storage with '
                                'computed checksum.')

    @test.attr(type="gate")
    def test_freezer_fs_backup_bad_checksum(self):
        # as above, but we'll ignore the computed checksum
        backup_args = ['freezer-agent',
                       '--path-to-backup',
                       self.source_tree.path,
                       '--container',
                       self.storage_tree.path,
                       '--backup-name',
                       self.freezer_backup_name,
                       '--storage',
                       'local',
                       '--consistency_check',
                       '--metadata-out',
                       self.metadata_out]

        self.run_subprocess(backup_args, 'Test backup to local storage.')

        # make a failing sha256 checksum (assuming no added path string)
        bad_checksum = '0' * 64

        # attempt to restore using the bad checksum
        restore_args = ['freezer-agent',
                        '--action',
                        'restore',
                        '--restore-abs-path',
                        self.dest_tree.path,
                        '--container',
                        self.storage_tree.path,
                        '--backup-name',
                        self.freezer_backup_name,
                        '--storage',
                        'local',
                        '--consistency_checksum',
                        bad_checksum]

        process = subprocess.Popen(restore_args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   env=self.environ, shell=False)
        out, err = process.communicate()

        # make sure the subprocess exist with an error due to checksum mismatch
        message = '{0} Output: {1} Error: {2}'.format(
            'Restore process should fail with checksum error.',
            out, err)
        self.assertEqual(1, process.returncode, message)
        self.assertEqual('', out, message)
        self.assertNotEqual('', err, message)
