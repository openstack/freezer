import json
from mock import patch

from horizon.utils.urlresolvers import reverse
import openstack_dashboard.test.helpers as helpers


@patch('freezer.apiclient.client')
class TestRestApi(helpers.TestCase):
    CLIENT_1 = {u'client': {u'hostname': u'jonas',
                            u'description': u'client description',
                            u'client_id': u'test-client',
                            u'config_ids': [u'fdaf2fwf2', u'fdsfdsfdsfs']},
                u'user_id': u'13c2b15308c04cdf86989ee7335eb504'}

    JSON_PREFIX = ')]}\',\n'

    def test_clients_get(self, client_mock):
        client_mock.Client().registration.list.return_value = [self.CLIENT_1]
        url = reverse("horizon:freezer_ui:api_clients")

        res = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, res.status_code)
        self.assertEqual('application/json', res['content-type'])
        self.assertEqual(self.JSON_PREFIX + json.dumps([self.CLIENT_1]),
                         res.content)
        # there is no get ALL api at the moment, so we just fetch a big number
        client_mock.Client().registration.list.assert_called_once_with(
            limit=9999)
