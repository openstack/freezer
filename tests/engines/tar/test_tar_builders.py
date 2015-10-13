import unittest
from freezer.engine.tar import tar_builders


class TestTarCommandBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = tar_builders\
            .TarCommandBuilder(".", "gzip", False, "gnutar")

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
        self.builder.set_encryption("encrypt_pass_file", "openssl")
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

    def test_build_every_arg_windows(self):
        self.builder = tar_builders\
            .TarCommandBuilder(".", "gzip", True, "gnutar")
        self.builder.set_listed_incremental("listed-file.tar")
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.builder.set_dereference("hard")
        self.builder.set_exclude("excluded_files")
        self.assertEquals(
            self.builder.build(),
            'gnutar -c -z --incremental --unlink-first --ignore-zeros '
            '--force-local --hard-dereference '
            '--listed-incremental=listed-file.tar --exclude="excluded_files"'
            ' . | openssl enc -aes-256-cfb -pass file:encrypt_pass_file')


class TestTarCommandRestoreBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = tar_builders.TarCommandRestoreBuilder(
            "restore_path", "gzip", False, "gnutar")

    def test(self):
        self.assertEquals(
            self.builder.build(),
            "gnutar -z --incremental --extract --unlink-first --ignore-zeros "
            "--warning=none --overwrite --directory restore_path")

    def test_dry_run(self):
        self.builder.set_dry_run()
        self.assertEquals(
            self.builder.build(),
            "gnutar -z --incremental --list --ignore-zeros --warning=none")

    def test_all_args(self):
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.assertEquals(
            self.builder.build(),
            "openssl enc -aes-256-cfb -pass file:encrypt_pass_file | gnutar "
            "-z --incremental --extract --unlink-first --ignore-zeros"
            " --warning=none --overwrite --directory restore_path")

    def test_all_args_windows(self):
        self.builder = tar_builders.TarCommandRestoreBuilder(
            "restore_path", "gzip", True, "gnutar")
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.assertEquals(
            self.builder.build(),
            'openssl enc -aes-256-cfb -pass file:encrypt_pass_file | '
            'gnutar -x -z --incremental --unlink-first --ignore-zeros '
            '-force-local')

    def test_get_tar_flag_from_algo(self):
        assert tar_builders.get_tar_flag_from_algo('gzip') == '-z'
        assert tar_builders.get_tar_flag_from_algo('bzip2') == '-j'
        assert tar_builders.get_tar_flag_from_algo('xz') == '-J'
