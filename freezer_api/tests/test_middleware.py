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
#from mock import Mock

import json
import falcon

from freezer_api.api.common import middleware

from common import FakeReqResp


class TestBackupMetadataDoc(unittest.TestCase):

    def setUp(self):
        self.json_translator = middleware.JSONTranslator()

    def test_process_request_with_no_body_returns_none(self):
        req = FakeReqResp()
        self.assertIsNone(self.json_translator.process_request(req, req))

    def test_process_request_with_positive_length_and_no_body_raises(self):
        req = FakeReqResp()
        req.content_length = 1
        self.assertRaises(falcon.HTTPBadRequest, self.json_translator.process_request, req, req)

    def test_process_response_with_no_result_returns_none(self):
        req = FakeReqResp()
        self.assertIsNone(self.json_translator.process_response(req, req, None))

    def test_process_response_create_correct_json_body(self):
        req = FakeReqResp()
        d = {'key1': 'value1', 'key2': 'value2'}
        req.context['result'] = d
        correct_json_body = json.dumps(d)
        self.json_translator.process_response(req, req, None)
        self.assertEqual(correct_json_body, req.body)

    def test_process_request_with_malformed_body_raises(self):
        req = FakeReqResp(body='{"key2": "value2",{ "key1": "value1"}')
        self.assertRaises(falcon.HTTPError, self.json_translator.process_request, req, req)
