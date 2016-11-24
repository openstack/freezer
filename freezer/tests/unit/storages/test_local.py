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

import shutil
import tempfile
import unittest

from freezer.storage import local
from freezer.utils import utils


class TestLocalStorage(unittest.TestCase):
    BACKUP_DIR_PREFIX = "freezer_test_backup_dir"
    FILES_DIR_PREFIX = "freezer_test_files_dir"
    WORK_DIR_PREFIX = "freezer_work_dir"
    HELLO = "Hello World!\n"
    temp = True

    def create_content(self, files_dir, file_name="file_1", text=HELLO):
        f = open(files_dir + "/" + file_name, 'w')
        f.write(text)
        f.close()

    def create_dirs(self):
        tmpdir = tempfile.mkdtemp()
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

    def test_prepare(self):
        backup_dir, files_dir, work_dir = self.create_dirs()
        storage = local.LocalStorage(backup_dir,
                                     work_dir,
                                     10000)
        storage.prepare()

    def test_info(self):
        backup_dir, files_dir, work_dir = self.create_dirs()
        storage = local.LocalStorage(backup_dir, work_dir, 10000)
        storage.info()
