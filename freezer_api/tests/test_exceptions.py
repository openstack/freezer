import unittest
from mock import Mock, patch

import falcon

from common import *
from freezer_api.common import exceptions


class TestExceptions(unittest.TestCase):

    def setUp(self):
        self.ex = Mock()
        self.ex.message = 'test exception'
        self.mock_req = Mock()
        self.mock_req.context = {}

    def test_FreezerAPIException(self):
        e = exceptions.FreezerAPIException(message='testing')
        self.assertRaises(falcon.HTTPError,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)

    def test_BadDataFormat(self):
        e = exceptions.BadDataFormat(message='testing')
        self.assertRaises(falcon.HTTPBadRequest,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)

    def test_DocumentExists(self):
        e = exceptions.DocumentExists(message='testing')
        self.assertRaises(falcon.HTTPConflict,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)

    def test_StorageEngineError(self):
        e = exceptions.StorageEngineError(message='testing')
        self.assertRaises(falcon.HTTPInternalServerError,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)

    def test_DocumentNotFound(self):
        e = exceptions.DocumentNotFound(message='testing')
        self.assertRaises(falcon.HTTPNotFound,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)

    def test_AccessForbidden(self):
        e = exceptions.AccessForbidden(message='testing')
        self.assertRaises(falcon.HTTPForbidden,
                          e.handle, self.ex, self.mock_req, self.mock_req, None)
