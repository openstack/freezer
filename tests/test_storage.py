import unittest
from freezer import storage


class TestBackup(unittest.TestCase):
    def test_backup_parse(self):
        self.assertRaises(ValueError, storage.Backup.parse, "asdfasdfasdf")
        backup = storage.Backup.parse("test_name_host_1234_0")
        self.assertEqual(backup.level, 0)
        self.assertEqual(backup.timestamp, 1234)
        self.assertEqual(backup.hostname_backup_name, "test_name_host")

    def test_backup_creation(self):
        backup = storage.Backup("name", 1234, 0)
        self.assertEqual(backup.hostname_backup_name, "name")
        self.assertEqual(backup.timestamp, 1234)
        self.assertEqual(backup.level, 0)
        self.assertEqual(backup.latest_update.level, 0)
        self.assertEqual(backup.latest_update.timestamp, 1234)
        self.assertEqual(backup.latest_update.hostname_backup_name, "name")
        self.assertEqual(len(backup.increments), 1)

    def test_backup_increment(self):
        backup = storage.Backup("name", 1234, 0)
        self.assertRaises(ValueError, backup.add_increment, backup)
        increment = storage.Backup("name", 4567, 1)
        backup.add_increment(increment)
        self.assertEqual(len(backup.increments), 2)

    def test__find_previous_backup(self):
        backup = storage.Backup("name", 1234, 0)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert b == backup

    def test__find_previous_backup_with_max_level(self):
        backup = storage.Backup("name", 1234, 0)
        i1 = storage.Backup("name", 1234, 1)
        i2 = storage.Backup("name", 1234, 2)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert not b

    def test__find_previous_backup_with_max_level_not_reached(self):
        backup = storage.Backup("name", 1234, 0)
        i1 = storage.Backup("name", 1234, 1)
        backup.add_increment(i1)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert b == i1

    def test__find_previous_backup_with_always_level_reached(self):
        backup = storage.Backup("name", 1234, 0)
        i1 = storage.Backup("name", 1234, 1)
        i2 = storage.Backup("name", 1234, 2)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, False, 2, 0)
        assert b == i1

    def test__find_previous_backup_with_always_level_reached_2(self):
        backup = storage.Backup("name", 1234, 0)
        i1 = storage.Backup("name", 1234, 1)
        i2 = storage.Backup("name", 1234, 2)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, False, 3, 0)
        assert b == i2
