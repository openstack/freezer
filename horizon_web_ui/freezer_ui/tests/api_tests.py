from django.conf import settings
from horizon_web_ui.freezer_ui.api import api
from mock import patch
from openstack_auth import utils
import openstack_dashboard.test.helpers as helpers


@patch('freezer.apiclient.client')
class TestApi(helpers.TestCase):
    CONFIG = {u'user_name': u'admin',
              u'config_id': u'053a62e0-66a9-4a1c-ba58-6b7348d22166',
              u'config_file': {u'start_datetime': u'1432736797',
                               u'repeat': u'1440',
                               u'max_priority': False,
                               u'encryption_password': u'secret',
                               u'src_file': u'fdsfsdds',
                               u'clients': [u'test-client'],
                               u'levels': 0,
                               u'proxy': u'',
                               u'container_name': u'dummy_container',
                               u'exclude': u'/tmp',
                               u'compression': u'gzip',
                               u'log_file': u'',
                               u'optimize': u'speed',
                               u'name': u'fdsfs'},
              u'user_id': u'13c2b15308c04cdf86989ee7335eb504'}

    def setUp(self):
        super(TestApi, self).setUp()

        # Usually this monkey patching happens in urls.py. This doesn't work
        # here because we never invoke urls.py in this test. So we have to do
        # it manually.
        utils.patch_middleware_get_user()

    def _setup_request(self):
        super(TestApi, self)._setup_request()
        # For some strange reason, Horizon sets the token to the token id
        # rather than the token object. This fixes it.
        self.request.session['token'] = self.token

    def assert_client_got_created(self, client_mock):
        client_mock.Client.assert_called_with(
            token=self.request.session['token'].id,
            auth_url=settings.OPENSTACK_KEYSTONE_URL,
            endpoint=settings.FREEZER_API_URL)

    def test_configuration_delete(self, client_mock):
        api.configuration_delete(
            self.request, u'053a62e0-66a9-4a1c-ba58-6b7348d22166')

        self.assert_client_got_created(client_mock)
        client_mock.Client().configs.delete.\
            assert_called_once_with(u'053a62e0-66a9-4a1c-ba58-6b7348d22166')

    def test_configuration_clone(self, client_mock):
        client_mock.Client().configs.get.return_value = [self.CONFIG]
        client_mock.Client().configs.\
            create.return_value = u'28124cf0-6cd3-4b38-a0e9-b6f41568fa37'

        result = api.configuration_clone(
            self.request, u'053a62e0-66a9-4a1c-ba58-6b7348d22166')

        self.assertEqual(result, u'28124cf0-6cd3-4b38-a0e9-b6f41568fa37')
        self.assert_client_got_created(client_mock)
        data = self.CONFIG[u'config_file']
        data['name'] = 'fdsfs_clone'
        client_mock.Client().configs.create.assert_called_once_with(data)

    def test_configuration_get(self, client_mock):
        client_mock.Client().configs.get.return_value = [self.CONFIG]

        result = api.configuration_get(
            self.request, u'053a62e0-66a9-4a1c-ba58-6b7348d22166')

        self.assertEqual(1, len(result))
        # Test if properties are accessible via object properties
        self.assertEqual(u'admin', result[0].user_name)
        # Test if nested properties are accessible via object properties
        self.assertEqual(u'1432736797', result[0].start_datetime)
