# Copyright 2017 Mirantis, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================

from copy import copy
import os
import uuid

from freezer.tests.integration import common


class TestBackupFSLocalRsync(common.TestFS):
    def test_backup_single_level(self):
        """
        - use the default source and destination trees in /tmp
        (see common.TestFS)
        - use temporary directory for backup storage
        - add some random data
        - check that trees don't match anymore
        - execute block based backup of source tree
        - execute restore into destination tree
        - check that source and destination trees match

        :return: non on success
        """
        self.source_tree.add_random_data()
        self.assertTreesMatchNot()

        with common.Temp_Tree() as storage_dir:
            backup_args = {
                'action': 'backup',
                'mode': 'fs',
                'path_to_backup': self.source_tree.path,
                'container': storage_dir.path,
                'storage': 'local',
                'engine': 'rsync',
                'max_segment_size': '67108864',
                'backup_name': uuid.uuid4().hex
            }

            restore_args = {
                'action': 'restore',
                'restore_abs_path': self.dest_tree.path,
                'backup_name': copy(backup_args['backup_name']),
                'storage': 'local',
                'engine': 'rsync',
                'container': storage_dir.path
            }
            result = common.execute_freezerc(backup_args)
            self.assertIsNotNone(result)
            result = common.execute_freezerc(restore_args)
            self.assertIsNotNone(result)
            self.assertTreesMatch()

    def test_backup_multiple_level(self):
        """
        - use the default source and destination trees in /tmp
        (see common.TestFS)
        - use temporary directory for backup storage
        - add some random data
        - check that trees don't match anymore
        - execute block based backup of source tree
        - modify data
        - execute backup again
        - delete some files
        - execute backup again
        - execute restore into destination tree
        - check that source and destination trees match

        :return: non on success
        """
        self.source_tree.add_random_data()
        self.assertTreesMatchNot()
        backup_name = uuid.uuid4().hex

        with common.Temp_Tree() as storage_dir:
            backup_args = {
                'action': 'backup',
                'mode': 'fs',
                'path_to_backup': self.source_tree.path,
                'container': storage_dir.path,
                'storage': 'local',
                'engine': 'rsync',
                'max_segment_size': '67108864',
                'backup_name': backup_name,
            }

            restore_args = {
                'action': 'restore',
                'restore_abs_path': self.dest_tree.path,
                'backup_name': backup_name,
                'storage': 'local',
                'engine': 'rsync',
                'container': storage_dir.path
            }
            result = common.execute_freezerc(backup_args)
            self.assertIsNotNone(result)
            self.source_tree.modify_random_files(2)
            result = common.execute_freezerc(backup_args)
            self.assertIsNotNone(result)
            self.source_tree.delete_random_files(1)
            result = common.execute_freezerc(backup_args)
            self.assertIsNotNone(result)
            result = common.execute_freezerc(restore_args)
            self.assertIsNotNone(result)
        self.assertTreesMatch()

    def test_backup_single_file(self):
        """
        - use the default source and destination trees in /tmp
        (see common.TestFS)
        - use temporary directory for backup storage
        - add one file with random data
        - check that trees don't match anymore
        - execute block based backup of single file
        - execute restore into destination tree
        - check that source and destination trees match

        :return: non on success
        """
        self.source_tree.add_random_data(ndir=0, nfile=1)
        self.assertTreesMatchNot()

        with common.Temp_Tree() as storage_dir:
            backup_args = {
                'action': 'backup',
                'mode': 'fs',
                'path_to_backup': os.path.join(
                    self.source_tree.path, self.source_tree.files[0]),
                'container': storage_dir.path,
                'storage': 'local',
                'engine': 'rsync',
                'max_segment_size': '67108864',
                'backup_name': uuid.uuid4().hex
            }

            restore_args = {
                'action': 'restore',
                'restore_abs_path': self.dest_tree.path,
                'backup_name': copy(backup_args['backup_name']),
                'storage': 'local',
                'engine': 'rsync',
                'container': storage_dir.path
            }
            result = common.execute_freezerc(backup_args)
            self.assertIsNotNone(result)
            result = common.execute_freezerc(restore_args)
            self.assertIsNotNone(result)
            self.assertTreesMatch()
