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

import json


class ApiClientException(Exception):
    def __init__(self, r):
        try:
            body = json.loads(r.text)
            message = "[*] Error {0}: {1}".format(
                r.status_code,
                body['description'])
        except:
            message = r
        super(ApiClientException, self).__init__(message)

    def __str__(self):
        return self.message


class MetadataCreationFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class MetadataGetFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class MetadataDeleteFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class AuthFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class MetadataUpdateFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class ConfigCreationFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class ConfigGetFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class ConfigDeleteFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)


class ConfigUpdateFailure(ApiClientException):
    def __init__(self, r=''):
        super(self.__class__, self).__init__(r)
