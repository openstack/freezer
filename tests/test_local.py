import tempfile
import shutil
import pytest

from freezer import local
from freezer import tar
from freezer import utils
import commons
import os

@pytest.mark.incremental
class TestLocalStorage(object):
    BACKUP_DIR_PREFIX = "freezer_test_backup_dir"
    FILES_DIR_PREFIX = "freezer_test_files_dir"
    HELLO = "Hello World!\n"
    temp = True

    def create_content(self, files_dir, file_name="file_1", text=HELLO):
        f = open(files_dir + "/" + file_name, 'w')
        f.write(text)
        f.close()

    def create_dirs(self, tmpdir):
        tmpdir = tmpdir.strpath
        if self.temp:
            backup_dir = tempfile.mkdtemp(
                dir=tmpdir, prefix=self.BACKUP_DIR_PREFIX)
            files_dir = tempfile.mkdtemp(
                dir=tmpdir, prefix=self.FILES_DIR_PREFIX)
        else:
            backup_dir = tmpdir + self.BACKUP_DIR_PREFIX
            files_dir = tmpdir + self.FILES_DIR_PREFIX
            utils.create_dir(backup_dir)
            utils.create_dir(files_dir)
        self.create_content(files_dir)
        return backup_dir, files_dir

    def remove_dirs(self, work_dir, files_dir, backup_dir):
        if self.temp:
            shutil.rmtree(work_dir)
            shutil.rmtree(files_dir)
            shutil.rmtree(backup_dir, ignore_errors=True)

    def remove_storage(self, backup_dir):
        shutil.rmtree(backup_dir)

    def test(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), ".")
        storage.backup(files_dir, "file_backup", builder)
        storage.get_backups()

    def test_is_ready(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        assert storage.is_ready()

    def test_prepare(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        assert storage.is_ready()
        self.remove_storage(backup_dir)
        assert not storage.is_ready()
        storage.prepare()
        assert storage.is_ready()

    def test_get_backups(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), ".")
        os.chdir(files_dir)
        storage.backup(files_dir, "file_backup", builder)
        backups = storage.get_backups()
        assert len(backups) == 1

    def test_incremental_backup(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), ".")
        os.chdir(files_dir)
        storage.backup(files_dir, "file_backup", builder)
        backups = storage.get_backups()
        assert len(backups) == 1
        backup = backups[0]
        self.create_content(files_dir, "file_2", "foo\n")
        storage.backup(files_dir, "file_backup", builder, backup)

    def test_incremental_restore(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), ".")
        os.chdir(files_dir)
        storage.backup(files_dir, "file_backup", builder)
        backups = storage.get_backups()
        assert len(backups) == 1
        backup = backups[0]
        self.create_content(files_dir, "file_2", "foo\n")
        storage.backup(files_dir, "file_backup", builder, backup)
        for path in os.listdir(files_dir):
            os.remove(files_dir + "/" + path)
        assert not os.listdir(files_dir)
        utils.create_dir(files_dir)
        backup = storage.get_backups()[0]
        builder = tar.TarCommandRestoreBuilder(commons.tar_path(), files_dir)
        storage.restore(backup.latest_update, files_dir, builder)
        files = os.listdir(files_dir)
        assert len(files) == 2
        with open(files_dir + "/file_1", "r") as file_1:
            assert self.HELLO == file_1.read()
        with open(files_dir + "/file_2", "r") as file_2:
            assert "foo\n" == file_2.read()

    def test_backup_file(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), "file_1")
        os.chdir(files_dir)
        storage.backup(files_dir + "/file_1", "file_backup", builder)
        for path in os.listdir(files_dir):
            os.remove(files_dir + "/" + path)
        assert not os.listdir(files_dir)
        utils.create_dir(files_dir)
        backup = storage.get_backups()[0]
        builder = tar.TarCommandRestoreBuilder(commons.tar_path(), files_dir)
        storage.restore(backup, files_dir, builder)
        files = os.listdir(files_dir)
        assert len(files) == 1

    def test_remove_backup(self, tmpdir):
        backup_dir, files_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir)
        builder = tar.TarCommandBuilder(commons.tar_path(), ".")
        os.chdir(files_dir)
        storage.backup(files_dir, "file_backup", builder)
        backups = storage.get_backups()
        assert len(backups) == 1
        storage.remove_backup(backups[0])
        backups = storage.get_backups()
        assert len(backups) == 0
