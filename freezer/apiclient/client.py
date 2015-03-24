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

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'freezer', '__init__.py')):
    sys.path.insert(0, possible_topdir)

import keystoneclient

from freezer.freezerclient.backups import BackupsManager


class Client(object):

    def __init__(self, version='1',
                 token=None,
                 username=None,
                 password=None,
                 tenant_name=None,
                 auth_url=None,
                 endpoint=None,
                 session=None):
        if endpoint is None:
                raise Exception('Missing endpoint information')
        self.endpoint = endpoint

        if token is not None:
            # validate the token ?
            self.token = token
        elif session is not None:
            pass
            # TODO: handle session auth
            # assert isinstance(session, keystoneclient.session.Session)
        else:
            self.username = username
            self.tenant_name = tenant_name
            kc = keystoneclient.v2_0.client.Client(
                username=username,
                password=password,
                tenant_name=tenant_name,
                auth_url=auth_url)
            self.token = kc.auth_token
        self.backups = BackupsManager(self)
