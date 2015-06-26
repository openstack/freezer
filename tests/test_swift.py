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

from commons import *
from freezer.storages.swiftstorage import SwiftStorage
from freezer.swift import (
    show_containers, show_objects, remove_obj_older_than,
    get_container_content, object_to_stream, _remove_object, remove_object)
import logging
import pytest
import time


class TestSwift:

    def test_show_containers(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        backup_opt.__dict__['list_containers'] = True
        show_containers(backup_opt.containers_list)

    def test_show_objects(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        backup_opt.__dict__['list_objects'] = True
        assert show_objects(backup_opt) is True

        backup_opt.__dict__['list_objects'] = False
        assert show_objects(backup_opt) is False

    def test__remove_object(self, monkeypatch):
        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakeclient = FakeSwiftClient()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt.sw_connector = fakeswclient
        faketime = FakeTime()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(time, 'sleep', faketime.sleep)

        assert _remove_object(fakeswclient, 'container', 'obj_name') is None

        fakeswclient.num_try = 59
        assert _remove_object(fakeswclient, 'container', 'obj_name') is None

        fakeswclient.num_try = 60
        pytest.raises(Exception, _remove_object, fakeclient, 'container', 'obj_name')

    def test_remove_object(self, monkeypatch):
        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakeclient = FakeSwiftClient()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt.sw_connector = fakeswclient
        faketime = FakeTime()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(time, 'sleep', faketime.sleep)

        assert remove_object(fakeswclient, 'freezer_segments', 'has_segments') is None

    def test_remove_obj_older_than(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakeclient = FakeSwiftClient1()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt.sw_connector = fakeswclient
        faketime = FakeTime()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(time, 'sleep', faketime.sleep)

        backup_opt = BackupOpt1()
        backup_opt.__dict__['remove_older_than'] = None
        backup_opt.__dict__['remove_from_date'] = '2014-12-03T23:23:23'
        assert remove_obj_older_than(backup_opt) is None

        backup_opt = BackupOpt1()
        backup_opt.__dict__['remove_older_than'] = 0
        backup_opt.__dict__['remove_from_date'] = None
        assert remove_obj_older_than(backup_opt) is None

        backup_opt = BackupOpt1()
        backup_opt.__dict__['remote_obj_list'] = []
        assert remove_obj_older_than(backup_opt) is None

    def test_get_container_content(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert get_container_content(backup_opt.client_manager,
                                     backup_opt.container) is not False
        assert get_container_content(backup_opt.client_manager,
                                     backup_opt.container) is not None

    def test_manifest_upload(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        file_prefix = '000000'
        manifest_meta_dict = {'x-object-manifest': 'test-x-object'}
        storage = SwiftStorage(backup_opt.client_manager, backup_opt.container)

        assert storage.upload_manifest(file_prefix, manifest_meta_dict) is None

        manifest_meta_dict = {}
        pytest.raises(
            Exception, storage.upload_manifest,
            file_prefix, manifest_meta_dict)

    def test_object_to_stream(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        obj_name = 'test-obj-name'
        fakemultiprocessing = FakeMultiProcessing1()
        backup_pipe_read = backup_pipe_write = fakemultiprocessing.Pipe()

        assert object_to_stream(
            backup_opt.container, backup_opt.client_manager,
            backup_pipe_write, backup_pipe_read, obj_name) is None
