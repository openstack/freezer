import unittest
from mock import Mock, patch

import time
import random
import falcon

from common import *
from freezer_api.common.exceptions import *

from freezer_api.api.v1 import actions as v1_actions


class TestClientsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_action_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_actions.ActionsCollectionResource(self.mock_db)

    def test_on_get_return_empty_list(self):
        self.mock_db.search_action.return_value = []
        expected_result = {'actions': []}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_get_return_correct_list(self):
        self.mock_db.search_action.return_value = [fake_action_0_doc, fake_action_1_doc]
        expected_result = {'actions': [fake_action_0_doc, fake_action_1_doc]}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_body(self):
        self.mock_db.add_action.return_value = fake_action_0_action_id
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    def test_on_post_inserts_correct_data(self):
        action = fake_action_0.copy()
        self.mock_req.context['doc'] = action
        self.mock_db.add_action.return_value = fake_action_0_action_id
        expected_result = {'action_id': fake_action_0_action_id}
        self.resource.on_post(self.mock_req, self.mock_req)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)
        assigned_action_id = self.mock_req.context['doc']['action_id']
        self.assertNotEqual(assigned_action_id, fake_action_0_action_id)

class TestClientsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_action_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_actions.ActionsResource(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_actions.ActionsResource)

    def test_on_get_return_no_result_and_404_when_not_found(self):
        self.mock_db.get_action.return_value = None
        self.resource.on_get(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.assertNotIn('result', self.mock_req.context)
        self.assertEqual(self.mock_req.status, falcon.HTTP_404)

    def test_on_get_return_correct_data(self):
        self.mock_db.get_action.return_value = fake_action_0
        self.resource.on_get(self.mock_req, self.mock_req, fake_action_0_action_id)
        result = self.mock_req.context['result']
        self.assertEqual(result, fake_action_0)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_delete_removes_proper_data(self):
        self.resource.on_delete(self.mock_req, self.mock_req, fake_action_0_action_id)
        result = self.mock_req.context['result']
        expected_result = {'action_id': fake_action_0_action_id}
        self.assertEquals(self.mock_req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_ok_with_some_fields(self, mock_time):
        mock_time.time.return_value = int(time.time())
        new_version = random.randint(0, 99)

        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'because': 'size_matters'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()

        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=patch_doc)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_no_timestamp_on_unknown_status(self, mock_time):
        timestamp = int(time.time())
        mock_time.time.return_value = timestamp
        new_version = random.randint(0, 99)
        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'status': 'happy'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()
        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=expected_patch)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_adds_correct_start_time(self, mock_time):
        timestamp = int(time.time())
        mock_time.time.return_value = timestamp
        new_version = random.randint(0, 99)
        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'status': 'started'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()
        expected_patch.update({"time_started": timestamp})

        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=expected_patch)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_adds_correct_end_time_on_abort(self, mock_time):
        timestamp = int(time.time())
        mock_time.time.return_value = timestamp
        new_version = random.randint(0, 99)
        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'status': 'aborted'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()
        expected_patch.update({"time_ended": timestamp})

        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=expected_patch)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_adds_correct_end_time_on_success(self, mock_time):
        timestamp = int(time.time())
        mock_time.time.return_value = timestamp
        new_version = random.randint(0, 99)
        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'status': 'success'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()
        expected_patch.update({"time_ended": timestamp})

        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=expected_patch)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    @patch('freezer_api.api.v1.actions.time')
    def test_on_patch_adds_correct_end_time_on_fail(self, mock_time):
        timestamp = int(time.time())
        mock_time.time.return_value = timestamp
        new_version = random.randint(0, 99)
        self.mock_db.update_action.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'status': 'fail'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()
        expected_patch.update({"time_ended": timestamp})

        expected_result = {'action_id': fake_action_0_action_id,
                           'patch': expected_patch,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_action_0_action_id)
        self.mock_db.update_action.assert_called_with(
            user_id=fake_action_0_user_id,
            action_id=fake_action_0_action_id,
            patch=expected_patch)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)