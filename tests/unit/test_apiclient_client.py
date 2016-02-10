"""
Copyright 2015 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import unittest
from mock import Mock, patch

from freezer.apiclient import client


class TestSupportFunctions(unittest.TestCase):

    @patch('freezer.apiclient.client.os')
    def test_env_return_env_var(self, mock_os):
        mock_os.environ = {'TEST_ENV_VAR': 'qwerty'}
        var = client.env('TEST_ENV_VAR')
        self.assertEquals(var, 'qwerty')

    @patch('freezer.apiclient.client.os')
    def test_env_return_default(self, mock_os):
        mock_os.environ = {}
        var = client.env('TEST_ENV_VAR')
        self.assertEquals(var, '')

    def test_guess_auth_version_returns_none(self):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = ''
        mock_opts.os_auth_url = ''
        self.assertRaises(Exception, client.guess_auth_version, mock_opts)

    def test_guess_auth_version_explicit_3(self):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '3'
        self.assertEquals(client.guess_auth_version(mock_opts), '3')

    def test_guess_auth_version_explicit_2(self):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '2.0'
        self.assertEquals(client.guess_auth_version(mock_opts), '2.0')

    def test_guess_auth_version_implicit_3(self):
        mock_opts = Mock()
        mock_opts.os_auth_url = 'http://whatever/v3'
        self.assertEquals(client.guess_auth_version(mock_opts), '3')

    def test_guess_auth_version_implicit_2(self):
        mock_opts = Mock()
        mock_opts.os_auth_url = 'http://whatever/v2.0'
        self.assertEquals(client.guess_auth_version(mock_opts), '2.0')

    @patch('freezer.apiclient.client.v3')
    @patch('freezer.apiclient.client.v2')
    def test_get_auth_plugin_v3_Password(self, mock_v2, mock_v3):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '3'
        mock_opts.os_user_name = 'myuser'
        mock_opts.os_token = ''
        client.get_auth_plugin(mock_opts)
        self.assertTrue(mock_v3.Password.called)

    @patch('freezer.apiclient.client.v3')
    @patch('freezer.apiclient.client.v2')
    def test_get_auth_plugin_v3_Token(self, mock_v2, mock_v3):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '3'
        mock_opts.os_username = ''
        mock_opts.os_token = 'mytoken'
        client.get_auth_plugin(mock_opts)
        self.assertTrue(mock_v3.Token.called)

    @patch('freezer.apiclient.client.v3')
    @patch('freezer.apiclient.client.v2')
    def test_get_auth_plugin_v2_Password(self, mock_v2, mock_v3):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '2.0'
        mock_opts.os_user_name = 'myuser'
        mock_opts.os_token = ''
        client.get_auth_plugin(mock_opts)
        self.assertTrue(mock_v2.Password.called)

    @patch('freezer.apiclient.client.v3')
    @patch('freezer.apiclient.client.v2')
    def test_get_auth_plugin_v2_Token(self, mock_v2, mock_v3):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '2.0'
        mock_opts.os_username = ''
        mock_opts.os_token = 'mytoken'
        client.get_auth_plugin(mock_opts)
        self.assertTrue(mock_v2.Token.called)

    @patch('freezer.apiclient.client.v3')
    @patch('freezer.apiclient.client.v2')
    def test_get_auth_plugin_raises_when_no_username_token(self, mock_v2, mock_v3):
        mock_opts = Mock()
        mock_opts.os_identity_api_version = '2.0'
        mock_opts.os_username = ''
        mock_opts.os_token = ''
        self.assertRaises(Exception, client.get_auth_plugin, mock_opts)


class TestClientMock(unittest.TestCase):

    @patch('freezer.apiclient.client.ksc_session')
    @patch('freezer.apiclient.client.get_auth_plugin')
    def test_client_new(self, mock_get_auth_plugin, mock_ksc_session):
        c = client.Client(opts=Mock(), endpoint='blabla')
        self.assertIsInstance(c, client.Client)

    @patch('freezer.apiclient.client.ksc_session')
    @patch('freezer.apiclient.client.get_auth_plugin')
    def test_client_new_with_kwargs(self, mock_get_auth_plugin, mock_ksc_session):
        kwargs = {'token': 'alpha',
                  'username': 'bravo',
                  'password': 'charlie',
                  'tenant_name': 'delta',
                  'auth_url': 'echo',
                  'session': 'foxtrot',
                  'endpoint': 'golf',
                  'version': 'hotel',
                  'cert': 'india',
                  'insecure': 'juliet',
                  'opts': Mock()}
        c = client.Client(**kwargs)
        self.assertIsInstance(c, client.Client)
        self.assertEqual('alpha', c.opts.os_token)
        self.assertEqual('bravo', c.opts.os_username)
        self.assertEqual('charlie', c.opts.os_password)
        self.assertEqual('delta', c.opts.os_tenant_name)
        self.assertEqual('echo', c.opts.os_auth_url)
        self.assertEqual('foxtrot', c._session)
        self.assertEqual('foxtrot', c.session)
        self.assertEqual('golf', c.endpoint)
        self.assertEqual('hotel', c.version)

    @patch('freezer.apiclient.client.ksc_session')
    @patch('freezer.apiclient.client.get_auth_plugin')
    def test_get_token(self, mock_get_auth_plugin, mock_ksc_session):
        mock_session = Mock()
        mock_session.get_token.return_value = 'antaniX2'
        c = client.Client(session=mock_session, endpoint='justtest', opts=Mock())
        self.assertIsInstance(c, client.Client)
        self.assertEquals(c.auth_token, 'antaniX2')

    @patch('freezer.apiclient.client.socket')
    @patch('freezer.apiclient.client.ksc_session')
    @patch('freezer.apiclient.client.get_auth_plugin')
    def test_get_client_id(self, mock_get_auth_plugin, mock_ksc_session, mock_socket):
        mock_socket.gethostname.return_value = 'parmenide'
        mock_session = Mock()
        mock_session.get_project_id.return_value = 'H2O'
        c = client.Client(session=mock_session, endpoint='justtest', opts=Mock())
        self.assertIsInstance(c, client.Client)
        self.assertEquals(c.client_id, 'H2O_parmenide')
