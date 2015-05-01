"""
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

import falcon
import logging


class FreezerAPIException(Exception):
    """
    Base Freezer API Exception
    """
    json_message = ({'error': 'Unknown exception occurred'})

    def __init__(self, message=None, resp_body={}):
        if message:
            self.message = message
        self.resp_body = resp_body
        logging.error(message)
        Exception.__init__(self, message)

    @staticmethod
    def handle(ex, req, resp, params):
        resp.status = falcon.HTTP_500
        req.context['result'] = {'error': 'internal server error'}


class BadDataFormat(FreezerAPIException):
    @staticmethod
    def handle(ex, req, resp, params):
        resp.status = falcon.HTTP_400
        ex.resp_body.update({'error': 'bad data format'})
        req.context['result'] = ex.resp_body


class DocumentExists(FreezerAPIException):
    @staticmethod
    def handle(ex, req, resp, params):
        resp.status = falcon.HTTP_409
        ex.resp_body.update({'error': 'document already exists'})
        req.context['result'] = ex.resp_body


class StorageEngineError(FreezerAPIException):
    @staticmethod
    def handle(ex, req, resp, params):
        resp.status = falcon.HTTP_500
        ex.resp_body.update({'error': 'storage engine'})
        req.context['result'] = ex.resp_body


exception_handlers_catalog = [
    BadDataFormat,
    DocumentExists,
    StorageEngineError
]
