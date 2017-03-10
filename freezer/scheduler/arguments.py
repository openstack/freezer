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

"""

import os
import sys

from freezer import __version__ as FREEZER_VERSION
from freezer.utils import winutils
from oslo_config import cfg
from oslo_log import log

CONF = cfg.CONF

if winutils.is_windows():
    DEFAULT_FREEZER_SCHEDULER_CONF_D = r'C:\.freezer\scheduler\conf.d'
else:
    DEFAULT_FREEZER_SCHEDULER_CONF_D = '/etc/freezer/scheduler/conf.d'


def add_filter():

    class NoLogFilter(log.logging.Filter):
        def filter(self, record):
            return False

    log_filter = NoLogFilter()
    log.logging.getLogger("apscheduler.scheduler").\
        addFilter(log_filter)
    log.logging.getLogger("apscheduler.executors.default").\
        addFilter(log_filter)
    log.logging.getLogger("requests.packages.urllib3.connectionpool").\
        addFilter(log_filter)


def env(*args, **kwargs):
    for v in args:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def get_common_opts():
    scheduler_conf_d = os.environ.get('FREEZER_SCHEDULER_CONF_D',
                                      DEFAULT_FREEZER_SCHEDULER_CONF_D)

    _COMMON = [
        cfg.StrOpt('client-id',
                   dest='client_id',
                   short='c',
                   help='Specifies the client_id used when contacting the '
                        'service.\n If not specified it will be automatically '
                        'created \n using the tenant-id and the machine '
                        'hostname.'),
        cfg.BoolOpt('no-api',
                    default=False,
                    dest='no_api',
                    short='n',
                    help='Prevents the scheduler from using the api service'),
        cfg.StrOpt('conf',
                   default=scheduler_conf_d,
                   dest='jobs_dir',
                   short='f',
                   help='Used to store/retrieve files on local storage, '
                        'including those exchanged with the api service. '
                        'Default value is {0} (Env: FREEZER_SCHEDULER_CONF_D)'
                   .format(scheduler_conf_d)),
        cfg.IntOpt('interval',
                   default=60,
                   dest='interval',
                   short='i',
                   help='Specifies the api-polling interval in seconds. '
                        'Defaults to 60 seconds'),
        cfg.BoolOpt('no-daemon',
                    default=False,
                    dest='no_daemon',
                    help='Prevents the scheduler from running in daemon mode'),
        cfg.BoolOpt('insecure',
                    default=False,
                    dest='insecure',
                    help='Initialize freezer scheduler with insecure mode'),
        cfg.BoolOpt('disable-exec',
                    default=False,
                    dest='disable_exec',
                    help='Allow Freezer Scheduler to deny jobs that execute '
                         'commands for security reasons'),
        cfg.IntOpt('concurrent_jobs',
                   default=1,
                   dest='concurrent_jobs',
                   help='Number of jobs that can be executed at the'
                        ' same time'),
    ]

    return _COMMON


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
        cfg.StrOpt('os-project-id',
                   default=env('OS_PROJECT_ID'),
                   help='Project id to scope to. Defaults to '
                        'env[OS_PROJECT_ID].',
                   dest='os_project_id'),
        cfg.StrOpt('os-project-name',
                   default=env('OS_PROJECT_NAME'),
                   help='Project name to scope to. Defaults to '
                        'env[OS_PROJECT_NAME].',
                   dest='os_project_name'),
        cfg.StrOpt('os-project-domain-id',
                   default=env('OS_PROJECT_DOMAIN_ID'),
                   help='Domain ID containing project. Defaults to '
                        'env[OS_PROJECT_DOMAIN_ID].',
                   dest='os_project_domain_id'),
        cfg.StrOpt('os-project-domain-name',
                   default=env('OS_PROJECT_DOMAIN_NAME'),
                   help='Domain name containing project. Defaults to '
                        'env[OS_PROJECT_DOMAIN_NAME].',
                   dest='os_project_domain_name'),
        cfg.StrOpt('os-user-domain-id',
                   default=env('OS_USER_DOMAIN_ID'),
                   help='User\'s domain id. Defaults to '
                        'env[OS_USER_DOMAIN_ID].',
                   dest='os_user_domain_id'),
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


def parse_args(choices):
    default_conf = cfg.find_config_files('freezer', 'scheduler', '.conf')
    CONF.register_cli_opts(get_common_opts())
    CONF.register_cli_opts(build_os_options())
    log.register_options(CONF)

    positional = [
        cfg.StrOpt('action',
                   choices=choices,
                   help='{0}'.format(choices), positional=True),

    ]
    CONF.register_cli_opts(positional)
    CONF(args=sys.argv[1:],
         project='freezer-scheduler',
         default_config_files=default_conf,
         version=FREEZER_VERSION
         )


def setup_logging():
    _DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                           'qpid=WARN', 'stevedore=WARN', 'oslo_log=INFO',
                           'iso8601=WARN', 'urllib3.connectionpool=WARN',
                           'requests.packages.urllib3.connectionpool=WARN',
                           'websocket=WARN', 'keystonemiddleware=WARN']

    _DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                       '%(levelname)s %(name)s '
                                       '[%(request_id)s %(user_identity)s] '
                                       '%(instance)s%(message)s')
    add_filter()
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    log.setup(CONF, 'freezer-scheduler', version=FREEZER_VERSION)


def list_opts():
    _opt = {
        None: get_common_opts()
    }
    return _opt.items()
