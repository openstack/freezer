"""Freezer Tar related tests

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

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

"""

from commons import *
from freezer.tar import get_tar_flag_from_algo

import os
import logging


class TestTar:

    def test_tar_restore_args_valid(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        fakeos = Os()
        monkeypatch.setattr(os.path, 'exists', fakeos.exists)

        backup_opt.dry_run = True

        fakeos1 = Os1()
        monkeypatch.setattr(os.path, 'exists', fakeos1.exists)
        backup_opt.dry_run = False

    def test_get_tar_flag_from_algo(self):
        assert get_tar_flag_from_algo('gzip') == '-z'
        assert get_tar_flag_from_algo('bzip2') == '-j'
        assert get_tar_flag_from_algo('xz') == '-J'
