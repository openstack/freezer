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
from freezer.swift import (create_containers, show_containers,
    show_objects, remove_obj_older_than, get_container_content,
    check_container_existance, get_swift_os_env,
    get_client, manifest_upload, add_object, get_containers_list,
    object_to_file, object_to_stream)
import os
import logging
import subprocess
import pytest
import time


class TestSwift:

    def test_create_containers(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert create_containers(backup_opt) is True

    def test_show_containers(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert show_containers(backup_opt) is True

        backup_opt.__dict__['list_container'] = False
        assert show_containers(backup_opt) is False

    def test_show_objects(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert show_objects(backup_opt) is True

        backup_opt.__dict__['remote_obj_list'] = None
        pytest.raises(Exception, show_objects, backup_opt)

        backup_opt.__dict__['list_objects'] = False
        assert show_objects(backup_opt) is False

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

        pytest.raises(Exception, remove_obj_older_than, backup_opt)

        backup_opt.__dict__['remove_older_than'] = False
        assert remove_obj_older_than(backup_opt) is False

        backup_opt = BackupOpt1()
        assert remove_obj_older_than(backup_opt) is None

    def test_get_container_content(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert get_container_content(backup_opt) is not False
        assert get_container_content(backup_opt) is not None

        backup_opt = BackupOpt1()
        backup_opt.container = False
        pytest.raises(Exception, get_container_content, backup_opt)

        fakeclient = FakeSwiftClient1()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt = BackupOpt1()
        backup_opt.sw_connector = fakeswclient
        pytest.raises(Exception, get_container_content, backup_opt)

    def test_check_container_existance(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert type(check_container_existance(backup_opt)) is dict

        backup_opt = BackupOpt1()
        backup_opt.container_segments = None
        pytest.raises(Exception, check_container_existance, backup_opt)

        backup_opt = BackupOpt1()
        backup_opt.container = 'test-abcd'
        backup_opt.container_segments = 'test-abcd-segments'
        assert type(check_container_existance(backup_opt)) is dict

    def test_get_client(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert isinstance(get_client(backup_opt), BackupOpt1) is True

    def test_manifest_upload(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        manifest_file = 'test-manifest-file'
        file_prefix = '000000'
        manifest_meta_dict = {'x-object-manifest': 'test-x-object'}

        assert manifest_upload(
            manifest_file, backup_opt,
            file_prefix, manifest_meta_dict) is None

        manifest_meta_dict = {}
        pytest.raises(
            Exception, manifest_upload, manifest_file, backup_opt,
            file_prefix, manifest_meta_dict)

    def test_add_object(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        fakemultiprocessing = FakeMultiProcessing()
        backup_queue = fakemultiprocessing.Queue()

        time_stamp = int(time.time())
        faketime = FakeTime()
        monkeypatch.setattr(time, 'sleep', faketime.sleep)
        absolute_file_path = '/tmp/test-abs-file-path'

        backup_opt = BackupOpt1()
        backup_opt.container = None

        pytest.raises(SystemExit, add_object, backup_opt, backup_queue,
                      absolute_file_path, time_stamp)

        fakeclient = FakeSwiftClient1()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt = BackupOpt1()
        backup_opt.sw_connector = fakeswclient
        pytest.raises(SystemExit, add_object, backup_opt, backup_queue,
                      absolute_file_path, time_stamp)

        backup_opt = BackupOpt1()
        absolute_file_path = None
        backup_queue = None
        pytest.raises(SystemExit, add_object, backup_opt, backup_queue,
                      absolute_file_path, time_stamp)

    def test_get_containers_list(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        assert isinstance(get_containers_list(backup_opt), BackupOpt1) is True

        fakeclient = FakeSwiftClient1()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        backup_opt = BackupOpt1()
        backup_opt.sw_connector = fakeswclient

        pytest.raises(Exception, get_containers_list, backup_opt)

    def test_object_to_file(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)

        file_name_abs_path = '/tmp/test-abs-file-path'
        assert object_to_file(backup_opt, file_name_abs_path) is True

        backup_opt = BackupOpt1()
        backup_opt.container = None
        pytest.raises(Exception, object_to_file, backup_opt, file_name_abs_path)

        os.unlink(file_name_abs_path)

    def test_object_to_stream(self, monkeypatch):

        backup_opt = BackupOpt1()
        fakelogging = FakeLogging()
        fakeclient = FakeSwiftClient()
        fakeconnector = fakeclient.client

        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)
        monkeypatch.setattr(swiftclient, 'client', fakeconnector)

        obj_name = 'test-obj-name'
        fakemultiprocessing = FakeMultiProcessing1()
        backup_pipe_read = backup_pipe_write = fakemultiprocessing.Pipe()

        backup_opt.container = None
        pytest.raises(Exception, object_to_stream,
            backup_opt, backup_pipe_write, backup_pipe_read, obj_name)

        backup_opt = BackupOpt1()
        assert object_to_stream(
            backup_opt, backup_pipe_write, backup_pipe_read, obj_name) is None
