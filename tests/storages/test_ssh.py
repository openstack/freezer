import unittest

from freezer.storage import ssh

class TestSshStorage(unittest.TestCase):

    def test_constructor(self):
        ssh.SshStorage.init = lambda x: x
        ssh.SshStorage(
            "test_dir", "test_work_dir", "test_key", "test_name", "test_ip",
            "teset_port")

    def test_info(self):
        ssh.SshStorage.init = lambda x: x
        ssh.SshStorage(
            "test_dir", "test_work_dir", "test_key", "test_name", "test_ip",
            "teset_port").info()
