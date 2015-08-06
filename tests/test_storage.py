import unittest
from freezer import storage
from freezer import tar
import mock


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

    def test_find(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            storage.Backup("host_backup", 1000, 0),
        ]
        result = t.find("host_backup")
        assert len(result) == 5
        for r in result:
            assert r.hostname_backup_name != "host_backup_f"

    def test_restore_latest_backup(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        last = storage.Backup("host_backup", 5000, 0)
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup", 2000, 0),
            storage.Backup("host_backup", 3000, 0),
            storage.Backup("host_backup", 4000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            last
        ]
        builder = tar.TarCommandRestoreBuilder("", "")
        self.assertRaises(ValueError, t.restore_latest, "test", ".", builder)
        t.restore = mock.Mock()
        t.restore_latest("host_backup", ".", builder)
        t.restore.assert_called_with(last, ".", builder)

    def test_find_latest_backup_respects_increments_timestamp(self):
        test_backup = storage.Backup("host_backup", 1000, 0)
        increment = storage.Backup("host_backup", 6000, 1)
        test_backup.add_increment(increment)
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = [
            test_backup,
            storage.Backup("host_backup", 2000, 0),
            storage.Backup("host_backup", 3000, 0),
            storage.Backup("host_backup", 4000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            storage.Backup("host_backup", 5000, 0),
        ]
        builder = tar.TarCommandRestoreBuilder("", "")
        t.restore = mock.Mock()
        t.restore_latest("host_backup", ".", builder)
        t.restore.assert_called_with(increment, ".", builder)

    def test_restore_from_date(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        backup_restore = storage.Backup("host_backup", 3000, 0)
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000, 0),
            storage.Backup("host_backup", 2000, 0),
            backup_restore,
            storage.Backup("host_backup", 4000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            storage.Backup("host_backup", 5000, 0),
        ]
        t.restore = mock.Mock()
        builder = tar.TarCommandRestoreBuilder("", "")
        t.restore_from_date("host_backup", ".", builder, 3234)
        t.restore.assert_called_with(backup_restore, ".", builder)

    def test_restore_from_date_increment(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        test_backup = storage.Backup("host_backup", 1000, 0)
        increment = storage.Backup("host_backup", 3200, 1)
        test_backup.add_increment(increment)
        t.get_backups.return_value = [
            test_backup,
            storage.Backup("host_backup", 4000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            storage.Backup("host_backup", 5000, 0),
        ]
        t.restore = mock.Mock()
        builder = tar.TarCommandRestoreBuilder("", "")
        t.restore_from_date("host_backup", ".", builder, 3234)
        t.restore.assert_called_with(increment, ".", builder)

    def test__get_backups_wrong_name(self):
        result = storage.Storage._get_backups(["hostname"])
        assert len(result) == 0
        result = storage.Storage._get_backups(["hostname_100_2"])
        assert len(result) == 0

    def test__get_backups_good_name(self):
        result = storage.Storage._get_backups(["host_backup_100_0"])
        assert len(result) == 1
        result = result[0]
        assert result.hostname_backup_name == "host_backup"
        assert result.timestamp == 100
        assert result.level == 0

    def test_remove_older_than(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        r1 = storage.Backup("host_backup", 1000, 0)
        r2 = storage.Backup("host_backup", 2000, 0)
        t.get_backups.return_value = [
            r1,
            r2,
            storage.Backup("host_backup", 3000, 0),
            storage.Backup("host_backup", 4000, 0),
            storage.Backup("host_backup_f", 1000, 0),
            storage.Backup("host_backup", 5000, 0),
        ]
        t.remove_backup = mock.Mock()
        t.remove_older_than(3000, "host_backup")
        t.remove_backup.assert_any_call(r1)
        t.remove_backup.assert_any_call(r2)
        assert t.remove_backup.call_count == 2
