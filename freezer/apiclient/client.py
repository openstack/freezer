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

client interface to the Freezer API
"""

import os
import socket

from keystoneauth1.identity import v2
from keystoneauth1.identity import v3
from keystoneauth1 import session as ksa_session
from oslo_config import cfg
from oslo_log import log

from freezer.apiclient import actions
from freezer.apiclient import backups
from freezer.apiclient import jobs
from freezer.apiclient import registration
from freezer.apiclient import sessions
from freezer.utils import utils

LOG = log.getLogger(__name__)

FREEZER_SERVICE_TYPE = 'backup'


def env(*vars, **kwargs):
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


class cached_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def build_os_options():
    osclient_opts = [
        cfg.StrOpt('os-username',
                   default=env('OS_USERNAME'),
                   help='Name used for authentication with the OpenStack '
                        'Identity service. Defaults to env[OS_USERNAME].',
                   dest='os_username'),
        cfg.StrOpt('os-password',
                   default=env('OS_PASSWORD'),
                   help='Password used for authentication with the OpenStack '
                        'Identity service. Defaults to env[OS_PASSWORD].',
                   dest='os_password'),
        cfg.StrOpt('os-project-name',
                   default=env('OS_PROJECT_NAME'),
                   help='Project name to scope to. Defaults to '
                        'env[OS_PROJECT_NAME].',
                   dest='os_project_name'),
        cfg.StrOpt('os-project-domain-name',
                   default=env('OS_PROJECT_DOMAIN_NAME'),
                   help='Domain name containing project. Defaults to '
                        'env[OS_PROJECT_DOMAIN_NAME].',
                   dest='os_project_domain_name'),
        cfg.StrOpt('os-user-domain-name',
                   default=env('OS_USER_DOMAIN_NAME'),
                   help='User\'s domain name. Defaults to '
                        'env[OS_USER_DOMAIN_NAME].',
                   dest='os_user_domain_name'),
        cfg.StrOpt('os-tenant-name',
                   default=env('OS_TENANT_NAME'),
                   help='Tenant to request authorization on. Defaults to '
                        'env[OS_TENANT_NAME].',
                   dest='os_tenant_name'),
        cfg.StrOpt('os-tenant-id',
                   default=env('OS_TENANT_ID'),
                   help='Tenant to request authorization on. Defaults to '
                        'env[OS_TENANT_ID].',
                   dest='os_tenant_id'),
        cfg.StrOpt('os-auth-url',
                   default=env('OS_AUTH_URL'),
                   help='Specify the Identity endpoint to use for '
                        'authentication. Defaults to env[OS_AUTH_URL].',
                   dest='os_auth_url'),
        cfg.StrOpt('os-backup-url',
                   default=env('OS_BACKUP_URL'),
                   help='Specify the Freezer backup service endpoint to use. '
                        'Defaults to env[OS_BACKUP_URL].',
                   dest='os_backup_url'),
        cfg.StrOpt('os-region-name',
                   default=env('OS_REGION_NAME'),
                   help='Specify the region to use. Defaults to '
                        'env[OS_REGION_NAME].',
                   dest='os_region_name'),
        cfg.StrOpt('os-token',
                   default=env('OS_TOKEN'),
                   help='Specify an existing token to use instead of '
                        'retrieving one via authentication '
                        '(e.g. with username & password). Defaults '
                        'to env[OS_TOKEN].',
                   dest='os_token'),
        cfg.StrOpt('os-identity-api-version',
                   default=env('OS_IDENTITY_API_VERSION'),
                   help='Identity API version: 2.0 or 3. '
                        'Defaults to env[OS_IDENTITY_API_VERSION]',
                   dest='os_identity_api_version'),
        cfg.StrOpt('os-endpoint-type',
                   choices=['public', 'publicURL', 'internal', 'internalURL',
                            'admin', 'adminURL'],
                   default=env('OS_ENDPOINT_TYPE') or 'public',
                   help='Endpoint type to select. Valid endpoint types: '
                        '"public" or "publicURL", "internal" or "internalURL",'
                        ' "admin" or "adminURL". Defaults to '
                        'env[OS_ENDPOINT_TYPE] or "public"',
                   dest='os_endpoint_type'),
        cfg.StrOpt('os-cert',
                   default=env('OS_CERT'),
                   help='Specify a cert file to use in verifying a TLS '
                        '(https) server certificate',
                   dest='os_cert'),
        cfg.StrOpt('os-cacert',
                   default=env('OS_CACERT'),
                   help='Specify a CA bundle file to use in verifying a TLS '
                        '(https) server certificate. Defaults to',
                   dest='os_cacert'),
    ]

    return osclient_opts


def guess_auth_version(opts):
    if opts.os_identity_api_version == '3':
        return '3'
    elif opts.os_identity_api_version == '2.0':
        return '2.0'
    elif opts.os_auth_url.endswith('v3'):
        return '3'
    elif opts.os_auth_url.endswith('v2.0'):
        return '2.0'
    raise Exception('Please provide valid keystone auth url with valid'
                    ' keystone api version to use')


def get_auth_plugin(opts):
    auth_version = guess_auth_version(opts)
    if opts.os_username:
        if auth_version == '3':
            return v3.Password(auth_url=opts.os_auth_url,
                               username=opts.os_username,
                               password=opts.os_password,
                               project_name=opts.os_project_name,
                               user_domain_name=opts.os_user_domain_name,
                               project_domain_name=opts.os_project_domain_name)
        elif auth_version == '2.0':
            return v2.Password(auth_url=opts.os_auth_url,
                               username=opts.os_username,
                               password=opts.os_password,
                               tenant_name=opts.os_tenant_name)
    elif opts.os_token:
        if auth_version == '3':
            return v3.Token(auth_url=opts.os_auth_url,
                            token=opts.os_token,
                            project_name=opts.os_project_name,
                            project_domain_name=opts.os_project_domain_name)
        elif auth_version == '2.0':
            return v2.Token(auth_url=opts.os_auth_url,
                            token=opts.os_token,
                            tenant_name=opts.os_tenant_name)
    raise Exception('Unable to determine correct auth method, please provide'
                    ' either username or token')


class Client(object):
    def __init__(self,
                 version='1',
                 token=None,
                 username=None,
                 password=None,
                 tenant_name=None,
                 auth_url=None,
                 session=None,
                 endpoint=None,
                 opts=None,
                 project_name=None,
                 user_domain_name=None,
                 project_domain_name=None,
                 cert=False,
                 cacert=False,
                 insecure=False):

        self.opts = opts
        # this creates a namespace for self.opts when the client is
        # created from other method rather than command line arguments.
        if self.opts is None:
            self.opts = utils.Namespace({})
        if token:
            self.opts.os_token = token
        if username:
            self.opts.os_username = username
        if password:
            self.opts.os_password = password
        if tenant_name:
            self.opts.os_tenant_name = tenant_name
        if auth_url:
            self.opts.os_auth_url = auth_url
        if endpoint:
            self.opts.os_backup_url = endpoint
        if project_name:
            self.opts.os_project_name = project_name
        if user_domain_name:
            self.opts.os_user_domain_name = user_domain_name
        if project_domain_name:
            self.opts.os_project_domain_name = project_domain_name
        if insecure:
            self.verify = False
        elif cacert:
            # verify arg in keystone sessions could be True/False/Path to cert
            self.verify = cacert
        else:
            self.verify = True
        if cert:
            self.opts.os_cert = cert

        self._session = session
        self.version = version

        self.backups = backups.BackupsManager(self, verify=self.verify)
        self.registration = registration.RegistrationManager(
            self, verify=self.verify)
        self.jobs = jobs.JobManager(self, verify=self.verify)
        self.actions = actions.ActionManager(self, verify=self.verify)
        self.sessions = sessions.SessionManager(self, verify=self.verify)

    @cached_property
    def session(self):
        if self._session:
            return self._session
        auth_plugin = get_auth_plugin(self.opts)
        return ksa_session.Session(auth=auth_plugin, verify=self.verify)

    @cached_property
    def endpoint(self):
        if self.opts.os_backup_url:
            return self.opts.os_backup_url
        else:
            auth_ref = self.session.auth.get_auth_ref(self.session)
            endpoint = auth_ref.service_catalog.url_for(
                service_type=FREEZER_SERVICE_TYPE,
                interface=self.opts.os_endpoint_type,
            )
        return endpoint

    @property
    def auth_token(self):
        return self.session.get_token()

    @cached_property
    def client_id(self):
        return '{0}_{1}'.format(self.session.get_project_id(),
                                socket.gethostname())
