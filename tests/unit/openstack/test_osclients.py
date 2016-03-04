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
import mock

from freezer.openstack import openstack
from freezer.openstack import osclients
from freezer.utils import utils


class TestOsClients(unittest.TestCase):

    fake_options = openstack.OpenstackOptions(
        user_name="user", tenant_name="tenant", project_name="project",
        auth_url="url", password="password", identity_api_version="3",
        insecure=False, cert='cert', verify=True)

    def test_init(self):
        osclients.ClientManager(self.fake_options, None, None, None)

    def test_create_cinder(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.create_cinder()

    def test_create_swift(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.create_swift()

    def test_create_nova(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.create_nova()

    def test_create_swift_public(self):
        options = openstack.OpenstackOptions(
            user_name="user", tenant_name="tenant", project_name="project",
            auth_url="url", password="password", identity_api_version="3",
            endpoint_type="adminURL", insecure=False, cert='cert',
            verify=True)
        client = osclients.ClientManager(options, None, None, None)
        client.create_swift()

    def test_dry_run(self):
        osclients.DryRunSwiftclientConnectionWrapper(mock.Mock())

    def test_get_cinder(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.get_cinder()

    def test_get_swift(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.get_swift()

    def get_glance(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.get_glance()

    def get_nova(self):
        client = osclients.ClientManager(self.fake_options, None, None, None)
        client.get_nova()
