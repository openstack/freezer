"""
Copyright 2015 Hewlett-Packard

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
import os
import sys
import uuid
import unittest
import tempfile
import shutil
import random
import hashlib
from copy import copy

lib_path = os.path.abspath(os.path.join('..', '..'))
sys.path.append(lib_path)

from freezer import arguments, main, swift

class BackupScenarioFS(unittest.TestCase):
    def create_tmp_tree(self, path):
        """
        freezer_test_XXXXXX
                          |-dir_foo
                          |       |-dir_bar
                          |       |       |
                          |       |       |-hello.lock
                          |       |       |-foo
                          |       |       |-bar
                          |       |       |-foobar
                          |       |
                          |       |-hello.lock
                          |       |-foo
                          |       |-bar
                          |       |-foobar
                          |
                          |-hello.lock
                          |-foo
                          |-bar
                          |-foobar
        """
        dir_path = copy(path)
        tmp_files = ['foo', 'bar', 'foobar', 'barfoo', 'foofoo', 'barbar', 'hello.lock']
        tmp_dirs = ['', 'dir_foo', 'dir_bar', 'dir_foobar', 'dir_barfoo', 'dir_foofoo', 'dir_barbar']
        self.tmp_files = []
        for fd in tmp_dirs:
            if fd:
                dir_path += os.path.sep + fd
                os.mkdir(dir_path)
            for fn in tmp_files:
                file_path = dir_path + os.path.sep + fn
                with open(file_path, 'w') as handle:
                    handle.write(fn + '\n' + dir_path + '\n')
                    handle.close()
                self.tmp_files.append(file_path)

    def hashfile(self, filepath):
        """
        Get GIT style sha1 hash for a file
        """
        filesize_bytes = os.path.getsize(filepath)
        hash_obj = hashlib.sha1()
        hash_obj.update(("blob %u\0" % filesize_bytes).encode('utf-8'))
        with open(filepath, 'rb') as handle:
            hash_obj.update(handle.read())
        return hash_obj.hexdigest()

    def snap_tmp_tree_sha1(self, file_list):
        hash_dict = {}
        for file_name in file_list:
            if os.path.isfile(file_name):
                hash_dict[file_name] = self.hashfile(file_name)
        return hash_dict

    def damage_tmp_tree(self, tmp_files):
        """
        Delete and modify random files from the tree file structure
        """
        # Delete 4 file
        tmp_files = copy(tmp_files)
        for nfile in range(4):
            fn = random.choice(tmp_files)
            os.unlink(fn)
            tmp_files.remove(fn)
            self.tmp_deleted.append(fn)
        # Change the content of 3 files
        for nfile in range(3):
            fn = random.choice(tmp_files)
            f = open(fn, 'w')
            f.write('foofoo\n')
            f.close()
            self.tmp_modified.append(fn)

    def setUp(self):
        self.tmp_files = []
        self.tmp_deleted = []
        self.tmp_modified = []
        self.tmp_path = tempfile.mkdtemp(prefix='freezer_test_')
        self.create_tmp_tree(self.tmp_path)

    def tearDown(self):
        # shutil.rmtree(self.tmp_path)
        pass

    def test_utils_methods(self):
        """
        Test functions that manipulate the files
        """
        dict_1 = self.snap_tmp_tree_sha1(self.tmp_files)
        self.damage_tmp_tree(self.tmp_files)
        dict_2 = self.snap_tmp_tree_sha1(self.tmp_files)
        self.assertEqual(len(self.tmp_files), len(dict_1))
        self.assertEqual(len(dict_1), len(self.tmp_deleted) + len(dict_2))
        for key in self.tmp_files:
            if key in self.tmp_deleted:
                self.assertFalse(os.path.isfile(key))
                self.assertFalse(key in dict_2)
            elif key in self.tmp_modified:
                self.assertTrue(os.path.isfile(key))
                self.assertNotEqual(key + dict_1[key], key + dict_2[key])
            else:
                self.assertTrue(os.path.isfile(key))
                self.assertEqual(key + dict_1[key], key + dict_2[key])

    def test_no_lvm_level0(self):
        """
        Maximum level filesystem backup

        freezerc --action backup
                 --path-to-backup /var/log
                 --backup-name rsync-var-log-test-XX
                 --container var-log-test-XX
        """
        max_retry = 5
        # Set arguments
        backup_args = {
            #'proxy' : '',
            'action' : 'backup',
            'src_file' : copy(self.tmp_path),
            'backup_name' : str(uuid.uuid4()),
            'container' : str(uuid.uuid4())
        }
        # Namespace backup_args object
        name_list = []
        retry = 0
        while backup_args['container'] not in name_list and retry < max_retry:
            ns_backup_args = main.freezer_main(backup_args)
            ns_backup_args = swift.get_container_content(ns_backup_args)
            name_list = [item['name'] for item in ns_backup_args.containers_list]
            retry += 1
        self.assertTrue(ns_backup_args.container in name_list)
        self.assertTrue(ns_backup_args.container_segments in name_list)
        fdict_before = self.snap_tmp_tree_sha1(self.tmp_files)
        self.damage_tmp_tree(self.tmp_files)
        # Restore
        restore_args = {
            #'proxy' : '',
            'action' : 'restore',
            'restore_abs_path' : copy(self.tmp_path),
            'backup_name' : copy(backup_args['backup_name']),
            'container' : copy(backup_args['container'])
        }
        main.freezer_main(restore_args)
        fdict_after = self.snap_tmp_tree_sha1(self.tmp_files)
        self.assertEqual(len(self.tmp_files), len(fdict_before))
        self.assertEqual(len(self.tmp_files), len(fdict_after))
        for key in self.tmp_files:
            self.assertTrue(os.path.isfile(key))
            self.assertEqual(key + fdict_before[key], key + fdict_after[key])

    def test_lvm_level0(self):
        """
        LVM snapshot filesystem backup

        freezerc --action backup
                 --lvm-srcvol /dev/freezer-test1-volgroup/freezer-test1-vol
                 --lvm-dirmount /tmp/freezer-test-lvm-snapshot
                 --lvm-volgroup freezer-test1-volgroup
                 --lvm-snapsize 1M
                 --file-to-backup /mnt/freezer-test-lvm/lvm_test_XXXX/
                 --container UUID
                 --exclude "\*.lock"
                 --backup-name UUID
        """
        max_retry = 5
        # Set arguments
        lvm_path = '/mnt/freezer-test-lvm'
        self.tmp_path = tempfile.mkdtemp(prefix='lvm_test_', dir=lvm_path)
        self.create_tmp_tree(self.tmp_path)
        backup_args = {
            #'proxy' : '',
            'action' : 'backup',
            'lvm_srcvol' : '/dev/freezer-test1-volgroup/freezer-test1-vol',
            'lvm_dirmount' : '/tmp/freezer-test-lvm-snapshot',
            'lvm_volgroup' : 'freezer-test1-volgroup',
            'lvm_snapsize' : '1M',
            'exclude' : '*.lock',
            'src_file' : copy(self.tmp_path),
            'backup_name' : str(uuid.uuid4()),
            'container' : str(uuid.uuid4())
        }
        # Call the actual BACKUP
        # Namespace backup_args object
        name_list = []
        retry = 0
        while backup_args['container'] not in name_list and retry < max_retry:
            ns_backup_args = main.freezer_main(backup_args)
            ns_backup_args = swift.get_container_content(ns_backup_args)
            name_list = [item['name'] for item in ns_backup_args.containers_list]
            retry += 1
        self.assertTrue(ns_backup_args.container in name_list)
        self.assertTrue(ns_backup_args.container_segments in name_list)
        # Create a file => SAH1 hash dictionary that will recored file
        # hashes before any files being modified or deleted
        fdict_before = self.snap_tmp_tree_sha1(self.tmp_files)
        # Delete and modify random files in the test directory
        # structure
        self.damage_tmp_tree(self.tmp_files)
        # RESTORE section
        # Create RESTORE action dictionary to be passed to
        # arguments.backup_arguments() they will emulate the
        # command line arguments
        restore_args = {
            #'proxy' : '',
            'action' : 'restore',
            'restore_abs_path' : copy(self.tmp_path),
            'backup_name' : copy(backup_args['backup_name']),
            'container' : copy(backup_args['container'])
        }
        # Call RESTORE on Freezer code base
        main.freezer_main(restore_args)
        fdict_after = self.snap_tmp_tree_sha1(self.tmp_files)
        self.assertEqual(len(self.tmp_files), len(fdict_before))
        # Check if cout of all original files match recovered files
        # plus the number of deleted .LOCK files which were not restored
        self.assertEqual(len(self.tmp_files), len(fdict_after) +
            len([x for x in self.tmp_deleted if x.endswith('.lock')]))
        for key in self.tmp_files:
            if key.endswith('.lock') and key in self.tmp_deleted:
                self.assertFalse(os.path.isfile(key))
            elif key.endswith('.lock') and key in self.tmp_modified:
                self.assertNotEqual(key + fdict_before[key], key + fdict_after[key])
            else:
                self.assertTrue(os.path.isfile(key))
                self.assertEqual(key + fdict_before[key], key + fdict_after[key])

if __name__ == '__main__':
    unittest.main()
