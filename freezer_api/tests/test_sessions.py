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

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================
"""

import unittest
from mock import Mock, patch

import random
import falcon

from common import *
from freezer_api.common.exceptions import *

from freezer_api.api.v1 import sessions as v1_sessions


class TestSessionsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_session_0['user_id']
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_sessions.SessionsCollectionResource(self.mock_db)

    def test_on_get_return_empty_list(self):
        self.mock_db.search_session.return_value = []
        expected_result = {'sessions': []}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_get_return_correct_list(self):
        self.mock_db.search_session.return_value = [get_fake_session_0(), get_fake_session_1()]
        expected_result = {'sessions': [get_fake_session_0(), get_fake_session_1()]}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_body(self):
        self.mock_db.add_session.return_value = fake_session_0['session_id']
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    def test_on_post_inserts_correct_data(self):
        session = get_fake_session_0()
        self.mock_req.context['doc'] = session
        self.mock_db.add_session.return_value = 'pjiofrdslaikfunr'
        expected_result = {'session_id': 'pjiofrdslaikfunr'}
        self.resource.on_post(self.mock_req, self.mock_req)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)
        # assigned_session_id = self.mock_req.context['doc']['session_id']
        # self.assertNotEqual(assigned_session_id, fake_session_0['session_id'])

class TestSessionsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_session_0['user_id']
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_sessions.SessionsResource(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_sessions.SessionsResource)

    def test_on_get_return_no_result_and_404_when_not_found(self):
        self.mock_db.get_session.return_value = None
        self.resource.on_get(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertNotIn('result', self.mock_req.context)
        self.assertEqual(self.mock_req.status, falcon.HTTP_404)

    def test_on_get_return_correct_data(self):
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.resource.on_get(self.mock_req, self.mock_req, fake_session_0['session_id'])
        result = self.mock_req.context['result']
        self.assertEqual(result, get_fake_session_0())
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_delete_removes_proper_data(self):
        self.resource.on_delete(self.mock_req, self.mock_req, fake_session_0['session_id'])
        result = self.mock_req.context['result']
        expected_result = {'session_id': fake_session_0['session_id']}
        self.assertEquals(self.mock_req.status, falcon.HTTP_204)
        self.assertEqual(result, expected_result)

    def test_on_patch_ok_with_some_fields(self):
        new_version = random.randint(0, 99)
        self.mock_db.update_session.return_value = new_version
        patch_doc = {'some_field': 'some_value',
                     'because': 'size_matters'}
        self.mock_req.context['doc'] = patch_doc

        expected_patch = patch_doc.copy()

        expected_result = {'session_id': fake_session_0['session_id'],
                           'version': new_version}

        self.resource.on_patch(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.mock_db.update_session.assert_called_with(
            user_id=fake_session_0['user_id'],
            session_id=fake_session_0['session_id'],
            patch_doc=patch_doc)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
        result = self.mock_req.context['result']
        self.assertEqual(result, expected_result)

    def test_on_post_ok(self):
        new_version = random.randint(0, 99)
        self.mock_db.replace_session.return_value = new_version
        session = get_fake_session_0()
        self.mock_req.context['doc'] = session
        expected_result = {'session_id': fake_session_0['session_id'],
                           'version': new_version}

        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    def test_on_post_raises_when_db_replace_session_raises(self):
        self.mock_db.replace_session.side_effect = AccessForbidden('regular test failure')
        session = get_fake_session_0()
        self.mock_req.context['doc'] = session
        self.assertRaises(AccessForbidden, self.resource.on_post,
                          self.mock_req,
                          self.mock_req,
                          fake_session_0['session_id'])


class TestSessionsAction(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_session_0['user_id']
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_sessions.SessionsAction(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_sessions.SessionsAction)

    def test_on_post_raises_when_unable_to_read_action_from_body(self):
        self.mock_req.context['doc'] = {}
        self.assertRaises(BadDataFormat, self.resource.on_post,
                          self.mock_req,
                          self.mock_req,
                          fake_session_0['session_id'])

    def test_on_post_start_action_ok(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version

        action = {"start": {
            "job_id": 'job_id_2',
            "current_tag": 5
        }}
        self.mock_req.context['doc'] = action
        expected_result = {'result': 'success',
                           'session_tag': 6}
        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_202)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    def test_on_post_start_action_raises_BadDataFormat_when_job_not_in_session(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version
        action = {"start": {
            "job_id": 'missedme',
            "current_tag": 5
        }}
        self.mock_req.context['doc'] = action
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req,
                          self.mock_req, fake_session_0['session_id'])

    def test_on_post_start_action_raises_BadDataFormat_when_current_tag_too_high(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version
        action = {"start": {
            "job_id": 'missedme',
            "current_tag": 6
        }}
        self.mock_req.context['doc'] = action
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req,
                          self.mock_req, fake_session_0['session_id'])

    def test_on_post_end_action_ok(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version
        action = {"end": {
            "job_id": 'job_id_2',
            "current_tag": 5,
            "result": "success"
        }}
        self.mock_req.context['doc'] = action
        expected_result = {'result': 'success',
                           'session_tag': 5}
        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_202)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    def test_on_post_end_action_raises_BadDataFormat_when_job_not_in_session(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version
        action = {"end": {
            "job_id": 'ahahahahah',
            "current_tag": 5,
            "result": "success"
        }}
        self.mock_req.context['doc'] = action
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req,
                          self.mock_req, fake_session_0['session_id'])

    def test_on_post_raises_MethodNotImplemented_when_methon_not_implemented(self):
        new_version = random.randint(0, 99)
        self.mock_db.get_session.return_value = get_fake_session_0()
        self.mock_db.update_session.return_value = new_version
        action = {"method_not_implemented": {
            "job_id": 'ahahahahah',
            "current_tag": 5,
            "result": "success"
        }}
        self.mock_req.context['doc'] = action
        self.assertRaises(MethodNotImplemented, self.resource.on_post, self.mock_req,
                          self.mock_req, fake_session_0['session_id'])

    @patch('freezer_api.api.v1.sessions.time')
    def test_on_post_start_succeeds_in_holdoff_if_tag_needs_not_increment(self, mock_time):
        mock_time.time.return_value = 1000
        new_version = random.randint(0, 99)
        session_doc = get_fake_session_0()
        session_doc['time_start'] = 999
        self.mock_db.get_session.return_value = session_doc
        self.mock_db.update_session.return_value = new_version
        action = {"start": {
            "job_id": 'job_id_2',
            "current_tag": 4
        }}
        self.mock_req.context['doc'] = action
        expected_result = {'result': 'success',
                           'session_tag': 5}
        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_202)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    @patch('freezer_api.api.v1.sessions.time')
    def test_on_post_start_replies_holdoff_if_tag_would_increment(self, mock_time):
        mock_time.time.return_value = 1000
        new_version = random.randint(0, 99)
        session_doc = get_fake_session_0()
        session_doc['time_start'] = 999
        self.mock_db.get_session.return_value = session_doc
        self.mock_db.update_session.return_value = new_version
        action = {"start": {
            "job_id": 'job_id_2',
            "current_tag": 5
        }}
        self.mock_req.context['doc'] = action
        expected_result = {'result': 'hold-off',
                           'session_tag': 5}
        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_202)
        self.assertEqual(self.mock_req.context['result'], expected_result)

    @patch('freezer_api.api.v1.sessions.time')
    def test_on_post_start_outofholdoff_replies_outofsync_when_tag_too_low(self, mock_time):
        mock_time.time.return_value = 2000
        new_version = random.randint(0, 99)
        session_doc = get_fake_session_0()
        session_doc['time_start'] = 999
        self.mock_db.get_session.return_value = session_doc
        self.mock_db.update_session.return_value = new_version
        action = {"start": {
            "job_id": 'job_id_2',
            "current_tag": 2
        }}
        self.mock_req.context['doc'] = action
        expected_result = {'result': 'out-of-sync',
                           'session_tag': 5}
        self.resource.on_post(self.mock_req, self.mock_req, fake_session_0['session_id'])
        self.assertEqual(self.mock_req.status, falcon.HTTP_202)
        self.assertEqual(self.mock_req.context['result'], expected_result)


class TestSessions(unittest.TestCase):

    def setUp(self):
        self.session_doc = {}
        self.session = v1_sessions.Session(self.session_doc)

    def test_create_resource(self):
        self.assertIsInstance(self.session, v1_sessions.Session)

    def test_overall_result_running(self):
        self.session_doc['jobs'] = {'job1': {'status': 'completed',
                                             'result': 'success'},
                                    'job2': {'status': 'running',
                                             'result': ''}}
        res = self.session.get_job_overall_result()
        self.assertEquals(res, 'running')

    def test_overall_result_fail(self):
        self.session_doc['jobs'] = {'job1': {'status': 'completed',
                                             'result': 'success'},
                                    'job2': {'status': 'completed',
                                             'result': 'fail'}}
        res = self.session.get_job_overall_result()
        self.assertEquals(res, 'fail')

    def test_overall_result_success(self):
        self.session_doc['jobs'] = {'job1': {'status': 'completed',
                                             'result': 'success'},
                                    'job2': {'status': 'completed',
                                             'result': 'success'}}
        res = self.session.get_job_overall_result()
        self.assertEquals(res, 'success')




class TestSessionsJobs(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.get_header.return_value = fake_session_0['user_id']
        self.mock_req.context = {}
        self.mock_req.status = falcon.HTTP_200
        self.resource = v1_sessions.SessionsJob(self.mock_db)

    def test_create_resource(self):
        self.assertIsInstance(self.resource, v1_sessions.SessionsJob)

    def test_on_put_adds_job_to_session_jobs(self):
        session = get_fake_session_0()
        job = get_fake_job_0()
        job_info = {job['job_id']: {'client_id': job['client_id'],
                    'status': job['job_schedule']['status'],
                    'result': job['job_schedule']['result'],
                    'time_started': job['job_schedule']['time_started'],
                    'time_ended': job['job_schedule']['time_ended']}}
        session_update_doc = {'jobs': job_info}

        self.mock_db.get_session.return_value = session
        self.mock_db.get_job.return_value = job

        self.resource.on_put(self.mock_req, self.mock_req,
                             session['session_id'],
                             job['job_id'])
        self.mock_db.update_session.assert_called_with(user_id=session['user_id'],
                                                       session_id=session['session_id'],
                                                       patch_doc=session_update_doc)

    def test_on_put_updates_job_with_session_info(self):
        session = get_fake_session_0()
        job = get_fake_job_0()

        self.mock_db.get_session.return_value = session
        self.mock_db.get_job.return_value = job

        job_update_doc = {
            'session_id': session['session_id'],
            'session_tag': session['session_tag'],
            'job_schedule': session['schedule']
        }

        self.resource.on_put(self.mock_req, self.mock_req,
                             session['session_id'],
                             job['job_id'])
        self.mock_db.update_job.assert_called_with(user_id=session['user_id'],
                               job_id=job['job_id'],
                               patch_doc=job_update_doc)

    def test_on_delete_removes_job_from_session_jobs(self):
        session = get_fake_session_0()
        updated_session = get_fake_session_1()
        job = get_fake_job_0()

        self.mock_db.get_session.return_value = session
        self.mock_db.get_job.return_value = job

        self.resource.on_delete(self.mock_req, self.mock_req,
                             session['session_id'],
                             'job_id_2')

        self.mock_db.replace_session.assert_called_with(user_id=session['user_id'],
                               session_id=session['session_id'],
                               doc=updated_session)

    def test_on_delete_removes_session_info_from_job_and_stops_job(self):
        session = get_fake_session_0()
        job = get_fake_job_0()

        self.mock_db.get_session.return_value = session
        self.mock_db.get_job.return_value = job

        job_update_doc = {
            'session_id': '',
            'session_tag': '',
            'job_event': 'stop'
        }

        self.resource.on_delete(self.mock_req, self.mock_req,
                             session['session_id'],
                             job['job_id'])

        self.mock_db.update_job.assert_called_with(user_id=session['user_id'],
                               job_id=job['job_id'],
                               patch_doc=job_update_doc)
