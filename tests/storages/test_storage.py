# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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
from freezer.storage import storage
import mock


class TestBackup(unittest.TestCase):
    def test_backup_parse(self):
        self.assertRaises(ValueError, storage.Backup._parse, "asdfasdfasdf")
        backup = storage.Backup._parse("test_name_host_1234_0")
        self.assertEqual(backup.level, 0)
        self.assertEqual(backup.timestamp, 1234)
        self.assertEqual(backup.hostname_backup_name, "test_name_host")

    def test_backup_creation(self):
        backup = storage.Backup("name", 1234)
        self.assertEqual(backup.hostname_backup_name, "name")
        self.assertEqual(backup.timestamp, 1234)
        self.assertEqual(backup.level, 0)
        self.assertEqual(backup.latest_update.level, 0)
        self.assertEqual(backup.latest_update.timestamp, 1234)
        self.assertEqual(backup.latest_update.hostname_backup_name, "name")
        self.assertEqual(len(backup.increments), 1)

    def test_backup_full_backup(self):
        ok = False
        try:
            storage.Backup("name", 1324, 0, "full_backup")
        except ValueError:
            ok = True
        if not ok:
            raise Exception("Should throw ValueError")

    def test_backup_increment(self):
        backup = storage.Backup("name", 1234)
        self.assertRaises(ValueError, backup.add_increment, backup)
        increment = storage.Backup("name", 4567, 1, backup)
        backup.add_increment(increment)
        self.assertEqual(len(backup.increments), 2)

    def test__find_previous_backup(self):
        backup = storage.Backup("name", 1234)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert b == backup

    def test__find_previous_backup_with_max_level(self):
        backup = storage.Backup("name", 1234)
        i1 = storage.Backup("name", 1234, 1, backup)
        i2 = storage.Backup("name", 1234, 2, backup)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert not b

    def test__find_previous_backup_with_max_level_not_reached(self):
        backup = storage.Backup("name", 1234)
        i1 = storage.Backup("name", 1234, 1, backup)
        backup.add_increment(i1)
        b = storage.Storage._find_previous_backup([backup], False, 2, False, 0)
        assert b == i1

    def test__find_previous_backup_with_always_level_reached(self):
        backup = storage.Backup("name", 1234)
        i1 = storage.Backup("name", 1234, 1, backup)
        i2 = storage.Backup("name", 1234, 2, backup)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, False, 2, 0)
        assert b == i1

    def test__find_previous_backup_with_always_level_reached_2(self):
        backup = storage.Backup("name", 1234)
        i1 = storage.Backup("name", 1234, 1, backup)
        i2 = storage.Backup("name", 1234, 2, backup)
        backup.add_increment(i1)
        backup.add_increment(i2)
        b = storage.Storage._find_previous_backup([backup], False, False, 3, 0)
        assert b == i2

    def test_add_increment_raises(self):
        backup = storage.Backup("name", 1234, level=3)
        self.assertRaises(ValueError, backup.add_increment, None)

    def test_find_all(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup_f", 1000),
            storage.Backup("host_backup", 1000),
        ]
        result = t.find_all("host_backup")
        assert len(result) == 5
        for r in result:
            assert r.hostname_backup_name != "host_backup_f"

    def test_restore_latest_backup(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        last = storage.Backup("host_backup", 5000)
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup", 2000),
            storage.Backup("host_backup", 3000),
            storage.Backup("host_backup", 4000),
            storage.Backup("host_backup_f", 1000),
            last
        ]
        self.assertRaises(IndexError, t.find_one, "")
        assert t.find_one("host_backup") == last

    def test_find_latest_backup_respects_increments_timestamp(self):
        test_backup = storage.Backup("host_backup", 5500)
        increment = storage.Backup("host_backup", 6000, 1, test_backup)
        test_backup.add_increment(increment)
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = [
            test_backup,
            storage.Backup("host_backup", 2000),
            storage.Backup("host_backup", 3000),
            storage.Backup("host_backup", 4000),
            storage.Backup("host_backup_f", 1000),
            storage.Backup("host_backup", 5000),
        ]
        assert t.find_one("host_backup") == increment

    def test_restore_from_date(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        backup_restore = storage.Backup("host_backup", 3000)
        t.get_backups.return_value = [
            storage.Backup("host_backup", 1000),
            storage.Backup("host_backup", 2000),
            backup_restore,
            storage.Backup("host_backup", 4000),
            storage.Backup("host_backup_f", 1000),
            storage.Backup("host_backup", 5000),
        ]
        assert t.find_one("host_backup", 3234) == backup_restore

    def test_restore_from_date_increment(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        test_backup = storage.Backup("host_backup", 1000)
        increment = storage.Backup("host_backup", 3200, 1, test_backup)
        test_backup.add_increment(increment)
        t.get_backups.return_value = [
            test_backup,
            storage.Backup("host_backup", 4000),
            storage.Backup("host_backup_f", 1000),
            storage.Backup("host_backup", 5000),
        ]
        assert t.find_one("host_backup", 3234) == increment

    def test__get_backups_wrong_name(self):
        result = storage.Backup.parse_backups(["hostname"])
        assert len(result) == 0
        result = storage.Backup.parse_backups(["hostname_100_2"])
        assert len(result) == 0

    def test__get_backups_good_name(self):
        result = storage.Backup.parse_backups(["host_backup_100_0"])
        assert len(result) == 1
        result = result[0]
        assert result.hostname_backup_name == "host_backup"
        assert result.timestamp == 100
        assert result.level == 0

    def test_remove_older_than(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        r1 = storage.Backup("host_backup", 1000)
        r2 = storage.Backup("host_backup", 2000)
        t.get_backups.return_value = [
            r1,
            r2,
            storage.Backup("host_backup", 3000),
            storage.Backup("host_backup", 4000),
            storage.Backup("host_backup_f", 1000),
            storage.Backup("host_backup", 5000),
        ]
        t.remove_backup = mock.Mock()
        t.remove_older_than(3000, "host_backup")
        t.remove_backup.assert_any_call(r1)
        t.remove_backup.assert_any_call(r2)
        assert t.remove_backup.call_count == 2

    def test_create_backup(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = []
        t._find_previous_backup = mock.Mock()
        t._find_previous_backup.return_value = \
            storage.Backup("host_backup", 3000, tar_meta=True)
        t.create_backup("", True, 12, False, False)

    def test_restart_always_level(self):
        t = storage.Storage()
        t.get_backups = mock.Mock()
        t.get_backups.return_value = []
        backup = storage.Backup("host_backup", 3000, tar_meta=True)
        t._find_previous_backup([backup], False, None, None, 10)
