import unittest
from mock import Mock, patch

import falcon


from common import *
from freezer_api.common.exceptions import *

from freezer_api.api.v1 import clients as v1_clients


class TestClientsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_data_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_clients.ClientsCollectionResource(self.mock_db)

    def test_on_get_return_empty_list(self):
        self.mock_db.get_client.return_value = []
        expected_result = {'clients': []}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_get_return_correct_list(self):
        self.mock_db.get_client.return_value = [fake_client_entry_0, fake_client_entry_1]
        expected_result = {'clients': [fake_client_entry_0, fake_client_entry_1]}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_body(self):
        self.mock_db.add_client.return_value = fake_client_info_0['client_id']
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    def test_on_post_inserts_correct_data(self):
        self.mock_req.context['doc'] = fake_client_info_0
        self.mock_db.add_client.return_value = fake_client_info_0['client_id']
        expected_result = {'client_id': fake_client_info_0['client_id']}
        self.resource.on_post(self.mock_req, self.mock_req)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)


class TestClientsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_data_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_clients.ClientsResource(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_clients.ClientsResource)

    def test_on_get_return_no_result_and_404_when_not_found(self):
        self.mock_db.get_client.return_value = []
        expected_result = []
        self.resource.on_get(self.mock_req, self.mock_req, fake_client_info_0['client_id'])
        self.assertNotIn('result', self.mock_req.context)
        self.assertEqual(self.mock_req.status, falcon.HTTP_404)

    def test_on_get_return_correct_data(self):
        self.mock_db.get_client.return_value = [fake_client_entry_0]
        expected_result = fake_client_entry_0
        self.resource.on_get(self.mock_req, self.mock_req, fake_client_info_0['client_id'])
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_delete_removes_proper_data(self):
        self.resource.on_delete(self.mock_req, self.mock_req, fake_client_info_0['client_id'])
        result = self.mock_req.context['result']
        expected_result = {'client_id': fake_client_info_0['client_id']}
        self.assertEquals(self.mock_req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)
