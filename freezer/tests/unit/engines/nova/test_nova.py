# (C) Copyright 2017 Mirantis, Inc.
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

import os
from unittest import mock

import ddt

from oslo_config import cfg
from oslo_serialization import jsonutils as json

from freezer.engine.nova import nova
from freezer.tests import commons
from freezer.utils import utils as freezer_utils


class FakeServer(object):
    def __init__(self, instance_id):
        self.id = instance_id


class FakeContextManager(object):
    def __init__(self, mock_file):
        self.mock_file = mock_file

    def __enter__(self):
        return self.mock_file

    def __exit__(self, *args):
        pass


class TestNovaEngine(commons.FreezerBaseTestCase):

    def setUp(self):
        super(TestNovaEngine, self).setUp()
        self.backup_opt = commons.BackupOpt1()
        self.project_id = "test-project-id"
        self.instance_names = ["instance-1", "instance-2", "instance-3"]
        if self.instance_names:
            self.instance_ids = [server for server in
                                 self.instance_names
                                 if server == self.backup_opt.nova_inst_name]
        self.instance_ids = ["instance-id-1", "instance-id-2", "instance-id-3"]

        self.instance_ids_str = json.dumps(self.instance_ids)
        servers_list = [FakeServer(instance_id) for instance_id in
                        self.instance_ids]

        self.mock_nova = mock.MagicMock()
        self.mock_nova.servers = mock.Mock(return_value=servers_list)
        self.backup_opt.client_manager = mock.MagicMock()
        self.backup_opt.client_manager.get_nova.return_value = self.mock_nova
        self.expected_backup_calls = [
            mock.call(
                backup_resource=inst_id,
                hostname_backup_name=os.path.join(self.backup_opt.backup_name,
                                                  inst_id),
                incremental=self.backup_opt.incremental,
                max_level=self.backup_opt.max_level,
                always_level=self.backup_opt.always_level,
                restart_always_level=self.backup_opt.restart_always_level)
            for inst_id in self.instance_ids]
        self.expected_restore_calls = [
            mock.call(
                hostname_backup_name=os.path.join(self.backup_opt.backup_name,
                                                  inst_id),
                restore_resource=inst_id,
                overwrite=self.backup_opt.overwrite,
                recent_to_date='test_timestamp')
            for inst_id in self.instance_ids]


class TestNovaEngineSwiftStorage(TestNovaEngine):
    def setUp(self):
        super(TestNovaEngineSwiftStorage, self).setUp()
        self.mock_swift_connection = mock.MagicMock()
        self.mock_swift_connection.get_object.return_value = (
            None, self.instance_ids_str)
        self.mock_swift_connection.put_object = mock.MagicMock()

        self.mock_swift_storage = mock.MagicMock()
        self.mock_swift_storage._type = 'swift'

        with mock.patch('openstack.connection.Connection'):
            self.engine = nova.NovaEngine(self.mock_swift_storage)
        self.engine.client = self.backup_opt.client_manager
        self.engine.client.create_swift = mock.Mock(
            return_value=self.mock_swift_connection)
        self.engine.backup = mock.Mock()
        self.engine.restore = mock.Mock()
        self.engine.nova = self.mock_nova

    def test_backup_nova_tenant_to_swift_storage(self):
        self.engine.backup_nova_tenant(self.project_id,
                                       self.backup_opt.backup_name,
                                       self.backup_opt.incremental,
                                       self.backup_opt.max_level,
                                       self.backup_opt.always_level,
                                       self.backup_opt.restart_always_level)

        self.mock_nova.servers.assert_called_once_with(details=False)
        self.engine.client.create_swift.assert_called_once()
        self.mock_swift_connection.put_object.assert_called_with(
            self.mock_swift_storage.storage_path,
            "project_test-project-id",
            self.instance_ids_str)
        self.engine.backup.assert_has_calls(self.expected_backup_calls,
                                            any_order=True)

    def test_restore_nova_tenant_from_swift_storage(self):
        self.engine.restore_nova_tenant(self.project_id,
                                        self.backup_opt.backup_name,
                                        self.backup_opt.overwrite,
                                        'test_timestamp')

        self.engine.client.create_swift.assert_called_once()
        self.mock_swift_connection.get_object.assert_called_with(
            self.mock_swift_storage.storage_path,
            "project_test-project-id")
        self.engine.restore.assert_has_calls(self.expected_restore_calls,
                                             any_order=True)

    def test_backup_nova_snapshot_wait_uses_conf_timeout(self):
        """The nova snapshot-active wait must use CONF.timeout rather than a
        hardcoded value so large instances whose snapshots take more than the
        previous hardcoded 100s do not spuriously fail.
        """
        CONF = cfg.CONF

        fake_server = mock.MagicMock()
        fake_server.task_state = None
        fake_image = mock.MagicMock()

        # Construct the engine OUTSIDE any try/except so a construction error
        # surfaces as a real failure rather than being swallowed.
        with mock.patch('openstack.connection.Connection'):
            engine = nova.NovaEngine(self.mock_swift_storage)
        engine.nova = mock.MagicMock()
        engine.nova.get_server.return_value = fake_server
        engine.nova.create_server_image.return_value = 'fake-image-id'
        engine.glance = mock.MagicMock()
        engine.glance.get_image.return_value = fake_image
        engine.client = mock.MagicMock()
        engine.temp_resource_prefix = 'tmp_'

        with mock.patch.object(freezer_utils, 'wait_for') as mock_wait:
            # backup_data is a generator; it must be iterated for its body to
            # run. The image-streaming code after the snapshot wait raises on
            # these mocks, but by then both wait_for calls are recorded.
            try:
                list(engine.backup_data('test-instance-id',
                                        'test-hostname/test-instance-id'))
            except Exception:
                pass

        # Isolate the image-active wait ("become active") from the earlier
        # task-finish wait ("to start the snapshot process"), and confirm it
        # was reached (guards against a trivially-passing test) and uses
        # CONF.timeout rather than a hardcoded value.
        snapshot_wait_calls = [
            c for c in mock_wait.call_args_list if 'become' in str(c)
        ]
        self.assertTrue(
            snapshot_wait_calls,
            "snapshot-active wait_for was never reached; test setup is wrong")
        # third positional arg is the timeout
        self.assertEqual(
            CONF.timeout, snapshot_wait_calls[0][0][2],
            "snapshot-active wait must use CONF.timeout, "
            "not a hardcoded value")


@ddt.ddt
class TestNovaEngineFSLikeStorage(TestNovaEngine):
    def setUp(self):
        super(TestNovaEngineFSLikeStorage, self).setUp()
        self.mock_file = mock.Mock()
        self.mock_file.readline = mock.Mock(return_value=self.instance_ids_str)
        self.mock_file.write = mock.Mock()

        self.mock_fslike_storage = mock.MagicMock()
        self.mock_fslike_storage.open = mock.Mock(
            return_value=FakeContextManager(self.mock_file))
        self.mock_fslike_storage.storage_path = 'test/storage/path'
        self.local_backup_file = os.path.join(
            self.mock_fslike_storage.storage_path,
            "project_test-project-id")

        with mock.patch('openstack.connection.Connection'):
            self.engine = nova.NovaEngine(self.mock_fslike_storage)
        self.engine.client = self.backup_opt.client_manager
        self.engine.backup = mock.Mock()
        self.engine.restore = mock.Mock()
        self.engine.nova = self.mock_nova

    @ddt.data('local', 'ssh')
    def test_backup_nova_tenant_to_fslike_storage(self,
                                                  storage_type):
        self.mock_fslike_storage._type = storage_type
        self.engine.backup_nova_tenant(self.project_id,
                                       self.backup_opt.backup_name,
                                       self.backup_opt.incremental,
                                       self.backup_opt.max_level,
                                       self.backup_opt.always_level,
                                       self.backup_opt.restart_always_level)

        self.mock_nova.servers.assert_called_once_with(details=False)
        self.mock_fslike_storage.open.assert_called_once_with(
            self.local_backup_file,
            'w')
        self.mock_file.write.assert_called_once_with(self.instance_ids_str)
        self.engine.backup.assert_has_calls(self.expected_backup_calls,
                                            any_order=True)

    @ddt.data('local', 'ssh')
    def test_restore_nova_tenant_from_fslike_storage(self,
                                                     storage_type):
        self.mock_fslike_storage._type = storage_type
        self.engine.restore_nova_tenant(self.project_id,
                                        self.backup_opt.backup_name,
                                        self.backup_opt.overwrite,
                                        'test_timestamp')

        self.mock_fslike_storage.open.assert_called_once_with(
            self.local_backup_file,
            'rb')
        self.mock_file.readline.assert_called_once_with()
        self.engine.restore.assert_has_calls(self.expected_restore_calls,
                                             any_order=True)


class TestNovaEngineS3Storage(TestNovaEngine):
    def setUp(self):
        super(TestNovaEngineS3Storage, self).setUp()
        self.mock_s3_storage = mock.MagicMock()
        self.mock_s3_storage.get_object()['Body'].read.return_value \
            = self.instance_ids_str
        self.mock_s3_storage.put_object = mock.MagicMock()
        self.mock_s3_storage.storage_path = 'test/storage/path'

        self.mock_s3_storage._type = 's3'

        with mock.patch('openstack.connection.Connection'):
            self.engine = nova.NovaEngine(self.mock_s3_storage)
        self.engine.client = self.backup_opt.client_manager
        self.engine.backup = mock.Mock()
        self.engine.restore = mock.Mock()
        self.engine.nova = self.mock_nova

    def test_backup_nova_tenant_to_s3_storage(self):
        self.engine.backup_nova_tenant(self.project_id,
                                       self.backup_opt.backup_name,
                                       self.backup_opt.incremental,
                                       self.backup_opt.max_level,
                                       self.backup_opt.always_level,
                                       self.backup_opt.restart_always_level)

        self.mock_nova.servers.assert_called_once_with(details=False)
        self.mock_s3_storage.put_object.assert_called_with(
            bucket_name=self.mock_s3_storage.get_bucket_name(),
            key="{0}/project_test-project-id".format(
                self.mock_s3_storage.get_object_prefix()),
            data=self.instance_ids_str
        )
        self.engine.backup.assert_has_calls(self.expected_backup_calls,
                                            any_order=True)

    def test_restore_nova_tenant_from_s3_storage(self):
        self.engine.restore_nova_tenant(self.project_id,
                                        self.backup_opt.backup_name,
                                        self.backup_opt.overwrite,
                                        'test_timestamp')

        self.mock_s3_storage.get_object.assert_called_with(
            bucket_name=self.mock_s3_storage.get_bucket_name(),
            key="{0}/project_test-project-id".format(
                self.mock_s3_storage.get_object_prefix()
            )
        )
        self.engine.restore.assert_has_calls(self.expected_restore_calls,
                                             any_order=True)
