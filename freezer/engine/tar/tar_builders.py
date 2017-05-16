"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Freezer Tar related functions
"""
from freezer.utils import utils


class TarCommandBuilder(object):
    """
    Building a tar cmd command. To build command invoke method build.
    """

    UNIX_TEMPLATE = (
        "{gnutar_path} --create {algo} --warning=none --no-check-device "
        "--one-file-system --preserve-permissions --same-owner "
        "--seek --ignore-failed-read")

    # local windows template
    WINDOWS_TEMPLATE = (
        "{gnutar_path} -c {algo} --incremental --unlink-first "
        "--ignore-zeros")

    LISTED_TEMPLATE = "{tar_command} --listed-incremental={listed_incremental}"

    DEREFERENCE_MODE = {'soft': '--dereference',
                        'hard': '--hard-dereference',
                        'all': '--hard-dereference --dereference'}

    def __init__(self, filepath, compression_algo, is_windows, tar_path=None):
        self.tar_path = tar_path or utils.tar_path()
        self.dereference = ''
        self.listed_incremental = None
        self.exclude = ''
        self.openssl_path = None
        self.encrypt_pass_file = None
        self.output_file = None
        self.filepath = filepath
        self.compression_algo = get_tar_flag_from_algo(compression_algo)
        self.is_windows = is_windows

    def set_listed_incremental(self, absolute_path):
        self.listed_incremental = absolute_path

    def set_exclude(self, exclude):
        self.exclude = exclude

    def set_dereference(self, mode):
        """
        Dereference hard and soft links according option choices.
            'soft' dereference soft links,
            'hard' dereference hardlinks,
            'all' dereference both.
            Default 'None'.
        """
        self.dereference = self.DEREFERENCE_MODE[mode]

    def set_encryption(self, encrypt_pass_file, openssl_path=None):
        self.openssl_path = openssl_path or utils.openssl_path()
        self.encrypt_pass_file = encrypt_pass_file

    def build(self):
        if self.is_windows:
            tar_command = self.WINDOWS_TEMPLATE.format(
                gnutar_path=self.tar_path, algo=self.compression_algo)
        else:
            tar_command = self.UNIX_TEMPLATE.format(
                gnutar_path=self.tar_path, algo=self.compression_algo)

        if self.dereference:
            tar_command = "{0} {1}".format(tar_command, self.dereference)

        if self.listed_incremental:
            tar_command = self.LISTED_TEMPLATE.format(
                tar_command=tar_command,
                listed_incremental=self.listed_incremental)

        if self.exclude:
            tar_command = '{tar_command} --exclude="{exclude}"'.format(
                tar_command=tar_command, exclude=self.exclude)

        tar_command = '{0} {1}'.format(tar_command, self.filepath)

        if self.encrypt_pass_file:
            openssl_cmd = "{openssl_path} enc -aes-256-cfb -pass file:{file}"\
                .format(openssl_path=self.openssl_path,
                        file=self.encrypt_pass_file)
            tar_command = '{0} | {1} && exit ${{PIPESTATUS[0]}}'\
                .format(tar_command, openssl_cmd)

        return tar_command


class TarCommandRestoreBuilder(object):
    WINDOWS_TEMPLATE = '{0} -x {1} --incremental --unlink-first ' \
        '--ignore-zeros'
    DRY_RUN_TEMPLATE = '{0} {1} --incremental --list ' \
        '--ignore-zeros --warning=none'
    UNIX_TEMPLATE = '{0} {1} --incremental --extract ' \
        '--ignore-zeros --warning=none --overwrite --directory {2}'
    OPENSSL_DEC = "{openssl_path} enc -d -aes-256-cfb -pass file:{file}"

    def __init__(self, restore_path, compression_algo, is_windows,
                 tar_path=None):
        self.dry_run = False
        self.is_windows = False
        self.openssl_path = None
        self.encrypt_pass_file = None
        self.tar_path = tar_path or utils.tar_path()
        self.restore_path = restore_path
        self.compression_algo = get_tar_flag_from_algo(compression_algo)
        self.is_windows = is_windows

    def set_dry_run(self):
        self.dry_run = True

    def set_encryption(self, encrypt_pass_file, openssl_path=None):
        self.openssl_path = openssl_path or utils.openssl_path()
        self.encrypt_pass_file = encrypt_pass_file

    def build(self):
        if self.dry_run:
            tar_command = self.DRY_RUN_TEMPLATE.format(self.tar_path,
                                                       self.compression_algo)
        elif self.is_windows:
            tar_command = self.WINDOWS_TEMPLATE.format(self.tar_path,
                                                       self.compression_algo)
        else:
            tar_command = self.UNIX_TEMPLATE.format(self.tar_path,
                                                    self.compression_algo,
                                                    self.restore_path)

        # Check if encryption file is provided and set the openssl decrypt
        # command accordingly
        if self.encrypt_pass_file:
            openssl_cmd = self.OPENSSL_DEC.format(
                openssl_path=self.openssl_path,
                file=self.encrypt_pass_file)
            tar_command = '{0} | {1} && exit ${{PIPESTATUS[0]}}'\
                .format(openssl_cmd, tar_command)
        return tar_command


def get_tar_flag_from_algo(compression):
    algo = {
        'gzip': '-z',
        'bzip2': '-j',
        'xz': '-J',
    }
    compression_exec = utils.get_executable_path(compression)
    if not compression_exec:
        raise Exception("Critical Error: {0} executable not found ".
                        format(compression))
    return algo.get(compression)
