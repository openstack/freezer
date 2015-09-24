import unittest
from freezer import osclients
from freezer import utils
from freezer.storage import swift
from freezer.storage import storage


class TestSwiftStorage(unittest.TestCase):

    def setUp(self):

        self.storage = swift.SwiftStorage(
            osclients.ClientManager(
                utils.OpenstackOptions.create_from_env()
            ),
            "freezer_ops-aw1ops1-gerrit0001.aw1.hpcloud.net",
            "/tmp/",
            100
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

        self.backup = storage.Backup("hostname_backup", 1000, tar_meta=True)
        self.backup_2 = storage.Backup("hostname_backup", 3000, tar_meta=True)
        self.increment = storage.Backup("hostname_backup", 2000,
                                        full_backup=self.backup,
                                        level=1,
                                        tar_meta=True)
        self.increment_2 = storage.Backup("hostname_backup", 4000,
                                          full_backup=self.backup_2,
                                          level=1,
                                          tar_meta=True)

    def test__get_backups(self):
        backups = storage.Backup.parse_backups(self.files)
        self.assertEqual(len(backups), 1)
        backup = backups[0]
        self.assertEqual(backup, self.backup)

    def test__get_backups_with_tar_only(self):
        backups = storage.Backup.parse_backups(
            ["tar_metadata_hostname_backup_1000_0"])
        self.assertEqual(len(backups), 0)

    def test__get_backups_without_tar(self):
        backups = storage.Backup.parse_backups(["hostname_backup_1000_0"])
        self.assertEqual(len(backups), 1)
        self.backup.tar_meta = False
        backup = backups[0]
        self.assertEqual(backup, self.backup)

    def test__get_backups_increment(self):
        backups = storage.Backup.parse_backups(self.increments)
        self.assertEqual(len(backups), 1)
        self.backup.add_increment(self.increment)
        backup = backups[0]
        self.assertEqual(backup, self.backup)

    def test__get_backups_increments(self):
        backups = storage.Backup.parse_backups(self.cycles_increments)
        self.assertEqual(len(backups), 2)
        self.backup.add_increment(self.increment)
        self.backup_2.add_increment(self.increment_2)
        self.assertEqual(backups[0], self.backup)
        self.assertEqual(backups[1], self.backup_2)
