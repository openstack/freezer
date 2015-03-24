"""Freezer swift.py related tests

Copyright 2014 Hewlett-Packard

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


import pytest

from common import *
from freezer_api.common.exceptions import *
from keystonemiddleware import auth_token


from freezer_api.cmd import api


class TestAPI:

    def patch_logging(self, monkeypatch):
        fakelogging = FakeLogging()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

    def test_auth_install(self, monkeypatch):
        self.patch_logging(monkeypatch)
        app = api.get_application(None)
        assert isinstance(app, auth_token.AuthProtocol)
