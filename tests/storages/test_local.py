import tempfile
import shutil
import pytest

from freezer.storage import local
from freezer import utils

@pytest.mark.incremental
class TestLocalStorage(object):
    BACKUP_DIR_PREFIX = "freezer_test_backup_dir"
    FILES_DIR_PREFIX = "freezer_test_files_dir"
    WORK_DIR_PREFIX = "freezer_work_dir"
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
            work_dir = tempfile.mkdtemp(
                dir=tmpdir, prefix=self.WORK_DIR_PREFIX)
        else:
            backup_dir = tmpdir + self.BACKUP_DIR_PREFIX
            files_dir = tmpdir + self.FILES_DIR_PREFIX
            work_dir = tmpdir + self.WORK_DIR_PREFIX
            utils.create_dir(backup_dir)
            utils.create_dir(work_dir)
            utils.create_dir(files_dir)
        self.create_content(files_dir)
        return backup_dir, files_dir, work_dir

    def remove_dirs(self, work_dir, files_dir, backup_dir):
        if self.temp:
            shutil.rmtree(work_dir)
            shutil.rmtree(files_dir)
            shutil.rmtree(backup_dir, ignore_errors=True)

    def remove_storage(self, backup_dir):
        shutil.rmtree(backup_dir)

    def test_prepare(self, tmpdir):
        backup_dir, files_dir, work_dir = self.create_dirs(tmpdir)
        storage = local.LocalStorage(backup_dir, work_dir)
        storage.prepare()
