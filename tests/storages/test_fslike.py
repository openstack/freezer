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
from freezer.storage import storage
import mock

class TestFsLikeStorage(object):
    def test_download_meta_file(self, tmpdir):
        t = fslike.FsLikeStorage(tmpdir.strpath, tmpdir.strpath)
        full_backup = storage.Backup("test", 2000)
        increment = storage.Backup("test", 2500, 9, full_backup)
        full_backup.add_increment(increment)
        backup = storage.Backup("test", 3000, 10, full_backup)
        t.get_file = mock.Mock()
        t.download_meta_file(backup)
