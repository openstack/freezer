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

import os
import sys

from openstackclient.identity import client as os_client

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'freezer', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from freezer.apiclient.backups import BackupsManager
from freezer.apiclient.registration import RegistrationManager
from freezer.apiclient.actions import ActionManager
from freezer.apiclient.configs import ConfigsManager
import exceptions


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
        self._auth = None
        self.backups = BackupsManager(self)
        self.registration = RegistrationManager(self)
        self.actions = ActionManager(self)
        self.configs = ConfigsManager(self)

    def _update_api_endpoint(self):
        services = self.auth.services.list()
        try:
            freezer_service = next(x for x in services if x.name == 'freezer')
        except:
            raise exceptions.AuthFailure(
                'freezer service not found in services list')
        endpoints = self.auth.endpoints.list()
        try:
            freezer_endpoint =\
                next(x for x in endpoints
                     if x.service_id == freezer_service.id)
        except:
            raise exceptions.AuthFailure(
                'freezer endpoint not found in endpoint list')
        self._endpoint = freezer_endpoint.publicurl

    @property
    def auth(self):
        if self._auth is None:
            if self.username and self.password:
                self._auth = os_client.IdentityClientv2(
                    auth_url=self.auth_url,
                    username=self.username,
                    password=self.password,
                    tenant_name=self.tenant_name)
            elif self.token:
                self._auth = os_client.IdentityClientv2(
                    endpoint=self.auth_url,
                    token=self.token)
            else:
                raise exceptions.AuthFailure("Missing auth credentials")
        return self._auth

    @property
    def auth_token(self):
        return self.auth.auth_token

    @property
    def endpoint(self):
        if self._endpoint is None:
            self._update_api_endpoint()
        return self._endpoint

    def api_exists(self):
        try:
            if self.endpoint is not None:
                return True
        except:
            return False
