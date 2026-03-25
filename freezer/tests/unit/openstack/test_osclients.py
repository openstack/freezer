# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.
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
from unittest import mock

from freezer.openstack import osclients


class TestOsClients(unittest.TestCase):
    def setUp(self):
        self.opts = osclients.OpenstackOpts(
            username="user", project_name="project",
            auth_url="url/v3", password="password", identity_api_version="3",
            insecure=False, cacert='cert', user_domain_name='Default',
            project_domain_name='Default').get_opts_dicts()
        self.client_manager = osclients.OSClientManager(**self.opts)

    @mock.patch('keystoneauth1.loading.get_plugin_loader')
    @mock.patch('openstack.connection.Connection')
    def test_client_manager_uses_trust(self, mock_connection, mock_loader):
        opts = osclients.OpenstackOpts(
            username="user", auth_url="url/v3", password="password",
            identity_api_version="3", insecure=False, cacert='cert',
            user_domain_name='Default', trust_id='fake_trust_123'
        ).get_opts_dicts()

        client_mgr = osclients.OSClientManager(**opts)

        mock_loader.assert_called_with('password')
        plugin = mock_loader.return_value
        plugin.load_from_options.assert_called_with(
            auth_url='url/v3',
            trust_id='fake_trust_123',
            username='user',
            password='password',
            user_domain_name='Default'
        )

        client_mgr.get_cinder()
        mock_connection.assert_called_with(session=client_mgr.sess)
        self.assertTrue(mock_connection.return_value.block_storage)

    @mock.patch('openstack.connection.Connection')
    def test_init(self, mock_connection):
        self.client_manager.get_cinder()

    @mock.patch('openstack.connection.Connection')
    def test_create_cinder(self, mock_connection):
        self.client_manager.create_cinder()

    def test_create_swift(self):
        self.client_manager.create_swift()

    @mock.patch('openstack.connection.Connection')
    def test_create_nova(self, mock_connection):
        self.client_manager.create_nova()

    @mock.patch('openstack.connection.Connection')
    def test_create_neutron(self, mock_connection):
        self.client_manager.create_neutron()

    def test_dry_run(self):
        osclients.DryRunSwiftclientConnectionWrapper(mock.Mock())

    @mock.patch('openstack.connection.Connection')
    def test_get_cinder(self, mock_connection):
        self.client_manager.get_cinder()

    def test_get_swift(self):
        self.client_manager.get_swift()

    @mock.patch('openstack.connection.Connection')
    def test_get_glance(self, mock_connection):
        self.client_manager.get_glance()

    @mock.patch('openstack.connection.Connection')
    def test_get_nova(self, mock_connection):
        self.client_manager.get_nova()

    @mock.patch('openstack.connection.Connection')
    def test_get_neutron(self, mock_connection):
        self.client_manager.get_neutron()


class TestOpenstackOpts(unittest.TestCase):
    def test_init(self):
        osclients.OpenstackOpts(auth_url='test', identity_api_version='3')
        osclients.OpenstackOpts(auth_url='test', identity_api_version=3)

    def test_init_raises(self):
        self.assertRaises(ValueError, osclients.OpenstackOpts,
                          auth_url='test', identity_api_version='2')
        self.assertRaises(ValueError, osclients.OpenstackOpts,
                          auth_url='test', identity_api_version=4)
