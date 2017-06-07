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

import mock

from freezer.openstack import osclients


class TestOsClients(unittest.TestCase):
    def setUp(self):
        self.opts = osclients.OpenstackOpts(
            username="user", tenant_name="tenant", project_name="project",
            auth_url="url/v3", password="password", identity_api_version="3",
            insecure=False, cacert='cert', user_domain_name='Default',
            project_domain_name='Default').get_opts_dicts()
        self.client_manager = osclients.OSClientManager(**self.opts)

    def test_init(self):
        self.client_manager.get_cinder()

    def test_create_cinder(self):
        self.client_manager.create_cinder()

    def test_create_swift(self):
        self.client_manager.create_swift()

    def test_create_nova(self):
        self.client_manager.create_nova()

    def test_create_neutron(self):
        self.client_manager.create_neutron()

    def test_dry_run(self):
        osclients.DryRunSwiftclientConnectionWrapper(mock.Mock())

    def test_get_cinder(self):
        self.client_manager.get_cinder()

    def test_get_swift(self):
        self.client_manager.get_swift()

    def test_get_glance(self):
        self.client_manager.get_glance()

    def test_get_nova(self):
        self.client_manager.get_nova()

    def test_get_neutron(self):
        self.client_manager.get_neutron()
