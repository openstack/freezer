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


from freezer.storage import fslike
from freezer.storage import base
import mock
import unittest
import tempfile

class TestFsLikeStorage(unittest.TestCase):
    def test_download_meta_file(self):
        tmpdir = tempfile.mkdtemp()
        t = fslike.FsLikeStorage(tmpdir, tmpdir, skip_prepare=True)
        full_backup = base.Backup(None, "test", 2000)
        increment = base.Backup(None, "test", 2500, 9, full_backup)
        full_backup.add_increment(increment)
        backup = base.Backup(None, "test", 3000, 10, full_backup)
        # t.get_file = mock.Mock()
        # t.download_meta_file(backup)
