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

from freezer.engine.tar import tar_builders
from freezer.utils import utils


class TestTarCommandBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = tar_builders.TarCommandBuilder(".", "gzip", False,
                                                      "gnutar")

    def test_build(self):
        self.assertEqual(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions "
            "--same-owner --seek --ignore-failed-read .")

    def test_build_listed(self):
        self.builder.set_listed_incremental("listed-file.tar")
        self.assertEqual(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions --same-owner --seek "
            "--ignore-failed-read --listed-incremental=listed-file.tar .")

    def test_build_every_arg(self):
        self.builder.set_listed_incremental("listed-file.tar")
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.builder.set_dereference("hard")
        self.builder.set_exclude("excluded_files")
        self.assertEqual(
            self.builder.build(),
            "gnutar --create -z --warning=none --no-check-device "
            "--one-file-system --preserve-permissions --same-owner "
            "--seek --ignore-failed-read --hard-dereference "
            "--listed-incremental=listed-file.tar "
            "--exclude=\"excluded_files\" . | openssl enc -aes-256-cfb -pass "
            "file:encrypt_pass_file && exit ${PIPESTATUS[0]}")

    def test_build_every_arg_windows(self):
        self.builder = tar_builders.TarCommandBuilder(".", "gzip", True,
                                                      "gnutar")
        self.builder.set_listed_incremental("listed-file.tar")
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.builder.set_dereference("hard")
        self.builder.set_exclude("excluded_files")
        self.assertEqual(
            self.builder.build(),
            'gnutar -c -z --incremental --unlink-first --ignore-zeros '
            '--hard-dereference --listed-incremental=listed-file.tar '
            '--exclude="excluded_files" . '
            '| openssl enc -aes-256-cfb -pass file:encrypt_pass_file '
            '&& exit ${PIPESTATUS[0]}')


class TestTarCommandRestoreBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = tar_builders.TarCommandRestoreBuilder(
            "restore_path", "gzip", False, "gnutar")

    def test(self):
        self.assertEqual(
            self.builder.build(),
            "gnutar -z --incremental --extract --ignore-zeros "
            "--warning=none --overwrite --directory restore_path")

    def test_dry_run(self):
        self.builder.set_dry_run()
        self.assertEqual(
            self.builder.build(),
            "gnutar -z --incremental --list --ignore-zeros --warning=none")

    def test_all_args(self):
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.assertEqual(
            self.builder.build(),
            "openssl enc -d -aes-256-cfb -pass file:encrypt_pass_file | "
            "gnutar -z --incremental --extract --ignore-zeros"
            " --warning=none --overwrite --directory restore_path "
            "&& exit ${PIPESTATUS[0]}")

    def test_all_args_windows(self):
        self.builder = tar_builders.TarCommandRestoreBuilder(
            "restore_path", "gzip", True, "gnutar")
        self.builder.set_encryption("encrypt_pass_file", "openssl")
        self.assertEqual(
            self.builder.build(),
            'openssl enc -d -aes-256-cfb -pass file:encrypt_pass_file '
            '| gnutar -x -z --incremental --unlink-first --ignore-zeros '
            '&& exit ${PIPESTATUS[0]}')

    def test_get_tar_flag_from_algo(self):
        assert tar_builders.get_tar_flag_from_algo('gzip') == '-z'
        assert tar_builders.get_tar_flag_from_algo('bzip2') == '-j'
        if not utils.is_bsd():
            assert tar_builders.get_tar_flag_from_algo('xz') == '-J'
