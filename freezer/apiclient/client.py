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

import socket

from openstackclient.identity import client as os_client

from backups import BackupsManager
from registration import RegistrationManager
from jobs import JobManager

import exceptions


class cached_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class Client(object):

    def __init__(self, version='1',
                 token=None,
                 username=None,
                 password=None,
                 tenant_name=None,
                 auth_url=None,
                 session=None,
                 endpoint=None):
        self.version = version
        self.token = token
        self.username = username
        self.tenant_name = tenant_name
        self.password = password
        self.auth_url = auth_url
        self._endpoint = endpoint
        self.session = session
        self.backups = BackupsManager(self)
        self.registration = RegistrationManager(self)
        self.jobs = JobManager(self)

    @cached_property
    def endpoint(self):
        if self._endpoint:
            return self._endpoint
        services = self.auth.services.list()
        try:
            freezer_service = next(x for x in services if x.name == 'freezer')
        except:
            raise exceptions.ApiClientException(
                'freezer service not found in services list')
        endpoints = self.auth.endpoints.list()
        try:
            freezer_endpoint =\
                next(x for x in endpoints
                     if x.service_id == freezer_service.id)
        except:
            raise exceptions.ApiClientException(
                'freezer endpoint not found in endpoint list')
        return freezer_endpoint.publicurl

    @cached_property
    def auth(self):
        if self.username and self.password:
            _auth = os_client.IdentityClientv2(
                auth_url=self.auth_url,
                username=self.username,
                password=self.password,
                tenant_name=self.tenant_name)
        elif self.token:
            _auth = os_client.IdentityClientv2(
                endpoint=self.auth_url,
                token=self.token)
        else:
            raise exceptions.ApiClientException("Missing auth credentials")
        return _auth

    @property
    def auth_token(self):
        return self.auth.auth_token

    def api_exists(self):
        try:
            if self.endpoint is not None:
                return True
        except:
            return False

    @cached_property
    def client_id(self):
        return '{0}_{1}'.format(self.auth.project_id, socket.gethostname())
