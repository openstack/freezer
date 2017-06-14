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

from tempest.lib import decorators

from freezer.tests.freezer_tempest_plugin.tests.api import base
from freezer.tests.integration import common


class TestFreezerCompressGzip(base.BaseFreezerTest):
    def __init__(self, *args, **kwargs):
        super(TestFreezerCompressGzip, self).__init__(*args, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        super(TestFreezerCompressGzip, self).setUp()

        # create a source tree to backup with a few empty files
        # (files must be empty to avoid encoding errors with pure random data)
        self.source_tree = common.Temp_Tree()
        self.source_tree.add_random_data(size=0)

        self.storage_tree = common.Temp_Tree()
        self.dest_tree = common.Temp_Tree()

        self.environ = super(TestFreezerCompressGzip, self).get_environ()

    def tearDown(self):
        super(TestFreezerCompressGzip, self).tearDown()

        self.source_tree.cleanup()
        self.dest_tree.cleanup()
        self.storage_tree.cleanup()

    def _backup(self, name, method):
        # perform a normal backup, with gzip specified
        backup_args = ['freezer-agent',
                       '--path-to-backup',
                       self.source_tree.path,
                       '--container',
                       self.storage_tree.path,
                       '--backup-name',
                       name,
                       '--storage',
                       'local',
                       '--compress',
                       method,
                       '--metadata-out',
                       os.path.join(self.storage_tree.path, 'metadata.json')]

        self.run_subprocess(backup_args, 'Test gzip backup to local storage.')

    def _restore(self, name, method):
        restore_args = ['freezer-agent',
                        '--action',
                        'restore',
                        '--restore-abs-path',
                        self.dest_tree.path,
                        '--container',
                        self.storage_tree.path,
                        '--backup-name',
                        name,
                        '--storage',
                        'local',
                        '--compress',
                        method]

        self.run_subprocess(restore_args, 'Test restore from local storage.')

    def _metadata(self):
        path = os.path.join(self.storage_tree.path, 'metadata.json')
        with open(path, 'r') as f:
            return json.load(f)

    def _file_get_mimetype(self, metadata):
        """Given some file metadata, find its mimetype using the file command

        :param metadata: the parsed json file metadata
        :return: the mimetype
        """
        """
        Data is stored like data/tar/localhost_False/1469786264/0_1469786264 so
        we need build the same directory structure.
        data: the directory that holds the backup data
        tar: the engine used to create backup
        localhost: the hostname of the machine where the backup was taken
        False: it should be backup name or False is backup is not provided
        1469786264: timestamp
        0_1469786264: level zero timestamp
        """
        data_file_path = 'data{0}{1}{0}{2}_{3}{0}{4}{0}{5}_{4}{0}data'.format(
            os.path.sep,
            "tar",  # currently we support only tar
            metadata['hostname'],
            metadata['backup_name'],
            metadata['time_stamp'],
            metadata['curr_backup_level']
        )
        data_file_path = os.path.join(self.storage_tree.path,
                                      data_file_path)
        self.assertEqual(True, os.path.exists(data_file_path))

        # run 'file' in brief mode to only output the values we want
        proc = subprocess.Popen(['file', '-b', '--mime-type', data_file_path],
                                stdout=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(0, proc.returncode)

        return out.strip()

    @decorators.attr(type="gate")
    def test_freezer_backup_compress_gzip(self):
        backup_name = 'freezer-test-backup-gzip-0'

        self._backup(backup_name, 'gzip')
        self._restore(backup_name, 'gzip')

        # metadata should show the correct algorithm
        metadata = self._metadata()
        self.assertIn('compression', metadata)
        self.assertEqual('gzip', metadata['compression'])

        # file utility should detect the correct mimetype
        gizp_mimetypes = ['application/gzip', 'application/x-gzip']
        mimetype = self._file_get_mimetype(metadata)
        self.assertIn(mimetype, gizp_mimetypes)

        # actual contents should be the same
        diff_args = ['diff', '-r', '-q',
                     self.source_tree.path,
                     self.dest_tree.path]
        self.run_subprocess(diff_args, 'Verify restored copy is identical to '
                                       'original.')

    @decorators.attr(type="gate")
    def test_freezer_backup_compress_bzip2(self):
        backup_name = 'freezer-test-backup-bzip2-0'

        self._backup(backup_name, 'bzip2')
        self._restore(backup_name, 'bzip2')

        metadata = self._metadata()
        self.assertIn('compression', metadata)
        self.assertEqual('bzip2', metadata['compression'])

        mimetype = self._file_get_mimetype(metadata)
        self.assertEqual('application/x-bzip2', mimetype)

        diff_args = ['diff', '-r', '-q',
                     self.source_tree.path,
                     self.dest_tree.path]
        self.run_subprocess(diff_args, 'Verify restored copy is identical to '
                                       'original.')

    @decorators.attr(type="gate")
    def test_freezer_backup_compress_xz(self):
        backup_name = 'freezer-test-backup-xz-0'

        self._backup(backup_name, 'xz')
        self._restore(backup_name, 'xz')

        metadata = self._metadata()
        self.assertIn('compression', metadata)
        self.assertEqual('xz', metadata['compression'])

        mimetype = self._file_get_mimetype(metadata)
        self.assertEqual('application/x-xz', mimetype)

        diff_args = ['diff', '-r', '-q',
                     self.source_tree.path,
                     self.dest_tree.path]
        self.run_subprocess(diff_args, 'Verify restored copy is identical to '
                                       'original.')
