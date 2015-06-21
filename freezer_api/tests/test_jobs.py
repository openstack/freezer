import unittest
from mock import Mock, patch

import random
import falcon

from common import *
from freezer_api.common.exceptions import *

from freezer_api.api.v1 import jobs as v1_jobs


class TestJobsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_job_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_jobs.JobsCollectionResource(self.mock_db)

    def test_on_get_return_empty_list(self):
        self.mock_db.search_job.return_value = []
        expected_result = {'jobs': []}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_get_return_correct_list(self):
        self.mock_db.search_job.return_value = [get_fake_job_0(), get_fake_job_1()]
        expected_result = {'jobs': [get_fake_job_0(), get_fake_job_1()]}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_body(self):
        self.mock_db.add_job.return_value = fake_job_0_job_id
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    def test_on_post_inserts_correct_data(self):
        job = get_fake_job_0()
        self.mock_req.context['doc'] = job
        self.mock_db.add_job.return_value = 'pjiofrdslaikfunr'
        expected_result = {'job_id': 'pjiofrdslaikfunr'}
        self.resource.on_post(self.mock_req, self.mock_req)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)
        # assigned_job_id = self.mock_req.context['doc']['job_id']
        # self.assertNotEqual(assigned_job_id, fake_job_0_job_id)

class TestJobsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_job_0_user_id
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_jobs.JobsResource(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_jobs.JobsResource)

    def test_on_get_return_no_result_and_404_when_not_found(self):
        self.mock_db.get_job.return_value = None
        self.resource.on_get(self.mock_req, self.mock_req, fake_job_0_job_id)
        self.assertNotIn('result', self.mock_req.context)
        self.assertEqual(self.mock_req.status, falcon.HTTP_404)

    def test_on_get_return_correct_data(self):
        self.mock_db.get_job.return_value = get_fake_job_0()
        self.resource.on_get(self.mock_req, self.mock_req, fake_job_0_job_id)
        result = self.mock_req.context['result']
        self.assertEqual(result, get_fake_job_0())
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_delete_removes_proper_data(self):
        self.resource.on_delete(self.mock_req, self.mock_req, fake_job_0_job_id)
        result = self.mock_req.context['result']
        expected_result = {'job_id': fake_job_0_job_id}
        self.assertEquals(self.mock_req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)

    def test_on_patch_ok_with_some_fields(self):
        new_version = random.randint(0, 99)
        self.mock_db.update_job.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'because': 'size_matters'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()

        expected_result = {'job_id': fake_job_0_job_id,
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_job_0_job_id)
        self.mock_db.update_job.assert_called_with(
            user_id=fake_job_0_user_id,
            job_id=fake_job_0_job_id,
            patch_doc=patch_doc)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    def test_on_post_ok(self):
        new_version = random.randint(0, 99)
        self.mock_db.replace_job.return_value = new_version
        job = get_fake_job_0()
        self.mock_req.context['doc'] = job
        expected_result = {'job_id': fake_job_0_job_id,
                           'version': new_version}

        self.resource.on_post(self.mock_req, self.mock_req, fake_job_0_job_id)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    def test_on_post_raises_when_db_replace_job_raises(self):
        self.mock_db.replace_job.side_effect = AccessForbidden('regular test failure')
        job = get_fake_job_0()
        self.mock_req.context['doc'] = job
        self.assertRaises(AccessForbidden, self.resource.on_post,
                          self.mock_req,
                          self.mock_req,
                          fake_job_0_job_id)
