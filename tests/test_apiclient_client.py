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

import unittest
from mock import Mock, patch

from freezer.apiclient import client
from freezer.apiclient import exceptions


class TestClientMock(unittest.TestCase):

    def create_mock_endpoint(self, service_id):
        m = Mock()
        m.service_id = service_id
        m.publicurl = 'http://frezerapiurl:9090'
        return m

    def create_mock_service(self, name, id):
        m = Mock()
        m.name = name
        m.id = id
        return m

    def setUp(self):
        mock_enpointlist_ok = [self.create_mock_endpoint('idqwerty'),
                               self.create_mock_endpoint('idfreak'),
                               self.create_mock_endpoint('blabla')]
        mock_servicelist_ok = [self.create_mock_service(name='glance', id='idqwerty'),
                               self.create_mock_service(name='freezer', id='idfreak')]
        self.mock_IdentityClientv2 = Mock()
        self.mock_IdentityClientv2.endpoints.list.return_value = mock_enpointlist_ok
        self.mock_IdentityClientv2.services.list.return_value = mock_servicelist_ok

    @patch('freezer.apiclient.client.os_client')
    def test_client_create_username(self, mock_os_client):
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        c = client.Client(username='myname',
                          password='mypasswd',
                          tenant_name='mytenant',
                          auth_url='http://whatever:35357/v2.0/')
        self.assertIsInstance(c, client.Client)
        self.assertEqual(c.api_endpoint, 'http://frezerapiurl:9090')

    @patch('freezer.apiclient.client.os_client')
    def test_client_create_token(self, mock_os_client):
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        c = client.Client(token='mytoken',
                          auth_url='http://whatever:35357/v2.0/')
        self.assertIsInstance(c, client.Client)
        self.assertEqual(c.api_endpoint, 'http://frezerapiurl:9090')

    @patch('freezer.apiclient.client.os_client')
    def test_client_error_no_credentials(self, mock_os_client):
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        self.assertRaises(exceptions.AuthFailure, client.Client, auth_url='http://whatever:35357/v2.0/')

    @patch('freezer.apiclient.client.os_client')
    def test_client_service_not_found(self, mock_os_client):
        mock_servicelist_bad = [self.create_mock_service(name='glance', id='idqwerty'),
                                self.create_mock_service(name='spanishinquisition', id='idfreak')]
        self.mock_IdentityClientv2.services.list.return_value = mock_servicelist_bad
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        self.assertRaises(exceptions.AuthFailure, client.Client, token='mytoken', auth_url='http://whatever:35357/v2.0/')

    @patch('freezer.apiclient.client.os_client')
    def test_client_endpoint_not_found(self, mock_os_client):
        mock_enpointlist_bad = [self.create_mock_endpoint('idqwerty'),
                               self.create_mock_endpoint('idfiasco'),
                               self.create_mock_endpoint('blabla')]
        self.mock_IdentityClientv2.endpoints.list.return_value = mock_enpointlist_bad
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        self.assertRaises(exceptions.AuthFailure, client.Client, token='mytoken', auth_url='http://whatever:35357/v2.0/')

    @patch('freezer.apiclient.client.os_client')
    def test_client_api_exists(self, mock_os_client):
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        c = client.Client(token='mytoken',
                          auth_url='http://whatever:35357/v2.0/')
        self.assertTrue(c.api_exists())

    @patch('freezer.apiclient.client.os_client')
    def test_client_auth_token(self, mock_os_client):
        self.mock_IdentityClientv2.auth_token = 'stotoken'
        mock_os_client.IdentityClientv2.return_value = self.mock_IdentityClientv2
        c = client.Client(token='mytoken',
                          auth_url='http://whatever:35357/v2.0/')
        self.assertEqual(c.auth_token, 'stotoken')
