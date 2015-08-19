import unittest
from freezer import tar


class TestTarCommandBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = tar.TarCommandBuilder("gnutar", ".", "gzip", False)

    def test_build(self):
        self.assertEquals(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions "
            "--same-owner --seek --ignore-failed-read .")

    def test_build_listed(self):
        self.builder.set_listed_incremental("listed-file.tar")
        self.assertEquals(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions --same-owner --seek "
            "--ignore-failed-read --listed-incremental=listed-file.tar .")

    def test_build_every_arg(self):
        self.builder.set_listed_incremental("listed-file.tar")
        self.builder.set_encryption("openssl", "encrypt_pass_file")
        self.builder.set_dereference("hard")
        self.builder.set_exclude("excluded_files")
        self.assertEquals(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions --same-owner "
            "--seek --ignore-failed-read --hard-dereference "
            "--listed-incremental=listed-file.tar "
            "--exclude=\"excluded_files\" . | openssl enc -aes-256-cfb -pass "
            "file:encrypt_pass_file")

class TestTarCommandRestoreBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = tar.TarCommandRestoreBuilder(
            "gnutar", "restore_path", "gzip", False)

    def test(self):
        self.assertEquals(
            self.builder.build(),
            "gnutar -z --incremental --extract --unlink-first --ignore-zeros "
            "--warning=none --overwrite --directory restore_path")
