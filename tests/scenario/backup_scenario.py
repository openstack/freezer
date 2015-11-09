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

"""

import os
import re
import sys
import uuid
import time
import unittest
import tempfile
import shutil
import random
import hashlib
import string
import time
from copy import copy

lib_path = os.path.abspath(os.path.join('..', '..'))
sys.path.append(lib_path)

from freezer import arguments, main, swift

class BackupScenarioFS(unittest.TestCase):
    def create_tmp_tree(self, path):
        """
        freezer_test_XXXXXX
            <tmp_files>
            ...........
            dir_foo
                <tmp_files>
                ...........
                dir_bar
                    <tmp_files>
                    ...........
                    dir_foobar
                        <tmp_files>
                        ...........
                        dir_barfoo
                            <tmp_files>
                            ...........
                            dir_foofoo
                                <tmp_files>
                                ...........
                                dir_barbar
                                    <tmp_files>
                                    ...........
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
        """
        Record in a dictionary all files' absulute paths and SHA1
        hashes so they can be compared taken before the backup and
        after the restore of a given level.
        """
        hash_dict = {}
        for file_name in file_list:
            if os.path.isfile(file_name):
                hash_dict[file_name] = self.hashfile(file_name)
        return hash_dict

    def damage_tmp_tree(self, tmp_files):
        """
        Delete and modify random files from the tree file structure
        """
        # Delete some files
        tmp_files = copy(tmp_files)
        for counter in range(0, 5):
            fn = random.choice(tmp_files)
            if fn not in self.tmp_deleted:
                os.unlink(fn)
                self.tmp_deleted.append(fn)
        # Change the content of a couple files
        for counter in range(0, 2):
            fn = random.choice(tmp_files)
            if fn not in self.tmp_deleted:
                f = open(fn, 'w')
                change_date = time.strftime('%Y-%m-%dT%H:%M:%S',
                    time.localtime()
                    )
                f.write('text changed on {}\n'.format(
                    change_date
                    ))
                f.close()
                self.tmp_modified.append(fn)

    def create_big_file(self, file_path, size):
        """
        Create test text file with random data and
        configurable size
        """
        buf = list(string.printable)
        with open(file_path, 'w') as handle:
            for i in range(size//len(buf)):
                random.shuffle(buf)
                handle.write('%s' % ''.join(buf))
            handle.close()

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
            'path_to_backup' : copy(self.tmp_path),
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
        # self.assertTrue(segments_name(ns_backup_args.container) in name_list)
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
            'path_to_backup' : copy(self.tmp_path),
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
        # self.assertTrue(segments_name(ns_backup_args.container) in name_list)
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

    def test_bandwith_limit(self):
        """
        Freezer upload/download speed limit test. We set a fixed 512KB/s speed and
        try to backup (upload) 1MB file na restore (download) the backup. Each of
        those action on avarage should not take more than 2s or less than 3s
        2s < EXEC_TIME < 3s. Without throttle it is normaly about 0.4s.

        freezerc --action backup
                 --path-to-backup /tmp/freezer_test_XXXX
                 --backup-name UUID
                 --container UUID
                 --upload-limit 524288

        freezerc --action restore
                 --path-to-backup /tmp/freezer_test_XXXX
                 --backup-name UUID
                 --container UUID
                 --download-limit 524288
        """
        # print '\nWorking in:', self.tmp_path
        # Set 512KB/s connection limit
        speed_limit_bytes = 512 * 1024
        time_low = 2
        abs_file_name = self.tmp_path + os.path.sep + 'limitfoo'
        # Create 1MB test text file with random data
        self.create_big_file(abs_file_name, 2 * speed_limit_bytes)
        # Freezer CLI for backup argument dictionary
        backup_args = {
            'action' : 'backup',
            'path_to_backup' : copy(self.tmp_path),
            'backup_name' : str(uuid.uuid4()),
            'container' : str(uuid.uuid4()),
            'upload_limit' : speed_limit_bytes
        }
        start_time = time.time()
        # Call Freezer CLI backup
        main.freezer_main(backup_args)
        end_time = time.time()
        # Calculate backup time in sec
        upload_time = end_time - start_time
        # print "\nUpload time: %g seconds" % upload_time
        # Test that time is longer than the theoretical 2 sec
        self.assertTrue(time_low < upload_time)
        # Delete test file
        os.unlink(abs_file_name)
        # Build dictionary for Freezer CLI restore
        restore_args = {
            'action' : 'restore',
            'restore_abs_path' : copy(self.tmp_path),
            'backup_name' : copy(backup_args['backup_name']),
            'container' : copy(backup_args['container']),
            'download_limit' : speed_limit_bytes
        }
        start_time = time.time()
        # Call the actual Freezer CLI restore
        main.freezer_main(restore_args)
        end_time = time.time()
        self.assertTrue(os.path.isfile(abs_file_name))
        # Calculate restore time in sec
        download_time = end_time - start_time
        # print "Download time: %g seconds" % download_time
        # sys.stdout.flush()
        # Test that time is longer than the theoretical 2 sec
        self.assertTrue(time_low < download_time)

    def test_lvm_incremental_level5(self):
        """
        Incremental LVM snapshots filesystem backup

        freezerc --action backup
                 --lvm-srcvol /dev/freezer-test1-volgroup/freezer-test1-vol
                 --lvm-dirmount /tmp/freezer-test-lvm-snapshot
                 --lvm-volgroup freezer-test1-volgroup
                 --lvm-snapsize 1M
                 --file-to-backup /mnt/freezer-test-lvm/lvm_test_XXXX/
                 --container UUID
                 --exclude "\*.lock"
                 --backup-name UUID
                 --max-level 5
        """
        # Set arguments
        lvm_path = '/mnt/freezer-test-lvm'
        self.tmp_path = tempfile.mkdtemp(prefix='lvm_test_', dir=lvm_path)
        self.create_tmp_tree(self.tmp_path)
        max_level = 5
        backup_args = {
            'action' : 'backup',
            'lvm_srcvol' : '/dev/freezer-test1-volgroup/freezer-test1-vol',
            'lvm_dirmount' : '/tmp/freezer-test-lvm-snapshot',
            'lvm_volgroup' : 'freezer-test1-volgroup',
            'lvm_snapsize' : '1M',
            'path_to_backup' : copy(self.tmp_path),
            'backup_name' : str(uuid.uuid4()),
            'container' : str(uuid.uuid4()),
            'max_level' : max_level
        }
        fdict_before = []
        # print ''
        for i in range(0, max_level):
            # print "TEST FILE CONTENT BEFORE BACKUP %s:" % i
            # print open(self.tmp_path + os.path.sep + 'foo', 'r').read()
            fdict_before.append(
                self.snap_tmp_tree_sha1(self.tmp_files)
                )
            ns_backup_args = main.freezer_main(backup_args)
            self.damage_tmp_tree(self.tmp_files)
            # time.sleep(2)
        # Filter only the container names from all other data
        ns_backup_args = swift.get_container_content(
            ns_backup_args.client_manager,
            ns_backup_args.container)
        name_list = [item['name'] for item in ns_backup_args]
        for counter in range(0, max_level):
            found_objects = [obj for obj in name_list if obj.endswith('_%s' % counter)]
            objects_str = ' '.join(found_objects)
            # print objects_str
            self.assertEqual('%s(%s)' % (objects_str,
                len(found_objects)), objects_str + '(2)')
            found_objects = sorted(found_objects)
            self.assertEqual(found_objects[1], found_objects[0][-len(found_objects[1]):])

        # From max_level-1 downto 0
        for i in range(max_level - 1, -1, -1):
            restore_level = i
            restore_epoch = re.findall('_(\d{10}?)_%s' % restore_level , ' '.join(name_list))[0]
            restore_epoch = int(restore_epoch) + 0
            restore_date = time.strftime('%Y-%m-%dT%H:%M:%S',
                time.localtime(int(restore_epoch))
                )
            # print 'Restore level:', restore_level, restore_epoch, restore_date
            # Remove all files in the whole testing directory
            shutil.rmtree(self.tmp_path)
            self.assertFalse(os.path.isdir(self.tmp_path))
            os.makedirs(self.tmp_path)
            # Build
            restore_args = {
                'action' : 'restore',
                'restore_abs_path' : copy(self.tmp_path),
                'backup_name' : copy(backup_args['backup_name']),
                'container' : copy(backup_args['container']),
                'restore_from_date' : restore_date
            }
            # Call RESTORE on Freezer code base
            main.freezer_main(restore_args)
            fdict_after = self.snap_tmp_tree_sha1(self.tmp_files)
            self.assertEqual(len(fdict_before[restore_level]), len(fdict_after))
            for key in fdict_before[restore_level]:
                self.assertTrue(os.path.isfile(key))
                self.assertEqual(key + fdict_before[restore_level][key], key + fdict_after[key])
            # print 'Just checked %s files' % len(fdict_after)


if __name__ == '__main__':
    unittest.main()
