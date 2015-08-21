"""Freezer main.py related tests

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

from commons import fake_create_job
from commons import FakeSys
from commons import BackupOpt1

from freezer.main import freezer_main
from freezer import job
import pytest
import sys


def test_freezer_main(monkeypatch):
    fake_sys = FakeSys()
    monkeypatch.setattr(job, 'create_job', fake_create_job)
    monkeypatch.setattr(sys, 'exit', fake_sys.fake_sys_exit)
    with pytest.raises(SystemExit):
        freezer_main()
    
    monkeypatch.setattr(job, 'create_job', fake_create_job)
    monkeypatch.setattr(sys, 'argv', FakeSys.fake_sys_argv())
    assert freezer_main() is not None
