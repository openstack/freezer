# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

from freezer.openstack import osclients
from freezer.storage import swift
from freezer.storage import base


class TestSwiftStorage(unittest.TestCase):

    def setUp(self):
        opts = osclients.OpenstackOpts.create_from_env().get_opts_dicts()
        self.storage = swift.SwiftStorage(
            osclients.OSClientManager(opts.pop('auth_url'),
                                      opts.pop('auth_method', 'password'),
                                      **opts
                                      ),
            "freezer_ops-aw1ops1-gerrit0001.aw1.hpcloud.net",
            "/tmp/",
            100, skip_prepare=True
        )

        self.files = [
            "tar_metadata_hostname_backup_1000_0",
            "hostname_backup_1000_0",
        ]

        self.increments = [
            "tar_metadata_hostname_backup_1000_0",
            "hostname_backup_1000_0",
            "tar_metadata_hostname_backup_2000_1",
            "hostname_backup_2000_1",
        ]

        self.cycles_increments = [
            "tar_metadata_hostname_backup_1000_0",
            "hostname_backup_1000_0",
            "tar_metadata_hostname_backup_2000_1",
            "hostname_backup_2000_1",
            "tar_metadata_hostname_backup_3000_0",
            "hostname_backup_3000_0",
            "tar_metadata_hostname_backup_4000_1",
            "hostname_backup_4000_1",
        ]

        self.backup = base.Backup(self.storage,
                                  "hostname_backup", 1000, tar_meta=True,)
        self.backup_2 = base.Backup(self.storage,
                                    "hostname_backup", 3000, tar_meta=True)
        self.increment = base.Backup(self.storage,
                                     "hostname_backup", 2000,
                                     full_backup=self.backup,
                                     level=1,
                                     tar_meta=True)
        self.increment_2 = base.Backup(self.storage,
                                       "hostname_backup", 4000,
                                       full_backup=self.backup_2,
                                       level=1,
                                       tar_meta=True)

    def test__get_backups(self):
        backups = base.Backup.parse_backups(self.files, self.storage)
        self.assertEqual(1, len(backups))
        backup = backups[0]
        self.assertEqual(self.backup, backup)

    def test__get_backups_with_tar_only(self):
        backups = base.Backup.parse_backups(
            ["tar_metadata_hostname_backup_1000_0"], self.storage)
        self.assertEqual(0, len(backups))

    def test__get_backups_without_tar(self):
        backups = base.Backup.parse_backups(["hostname_backup_1000_0"],
                                            self.storage)
        self.assertEqual(1, len(backups))
        self.backup.tar_meta = False
        backup = backups[0]
        self.assertEqual(self.backup, backup)

    def test__get_backups_increment(self):
        backups = base.Backup.parse_backups(self.increments, self.storage)
        self.assertEqual(1, len(backups))
        self.backup.add_increment(self.increment)
        backup = backups[0]
        self.assertEqual(self.backup, backup)

    def test__get_backups_increments(self):
        backups = base.Backup.parse_backups(self.cycles_increments,
                                            self.storage)
        self.assertEqual(2, len(backups))
        self.backup.add_increment(self.increment)
        self.backup_2.add_increment(self.increment_2)
        self.assertEqual(self.backup, backups[0])
        self.assertEqual(self.backup_2, backups[1])
