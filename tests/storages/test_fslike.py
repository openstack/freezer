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
