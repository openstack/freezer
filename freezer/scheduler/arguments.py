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

import argparse
from prettytable import PrettyTable

SCHEDULER_CONF_D = '/etc/freezer/scheduler/conf.d'


class OpenstackOptions(object):
    def __init__(self, args, default_dict={}):
        self.username = args.os_username or\
            default_dict.get('OS_USERNAME', None)
        self.tenant_name = args.os_tenant_name or\
            default_dict.get('OS_TENANT_NAME', None)
        self.auth_url = args.os_auth_url or\
            default_dict.get('OS_AUTH_URL', None)
        self.password = args.os_password or\
            default_dict.get('OS_PASSWORD', None)
        self.tenant_id = args.os_tenant_id or\
            default_dict.get('OS_TENANT_ID', None)
        self.region_name = args.os_region_name or\
            default_dict.get('OS_REGION_NAME', None)
        self.endpoint = args.os_endpoint or\
            default_dict.get('OS_SERVICE_ENDPOINT', None)
        if not self.is_valid():
            raise Exception('ERROR: OS Options not valid: {0}'.
                            format(self.reason()))

    def __str__(self):
        table = PrettyTable(["variable", "value"])
        table.add_row(['username', self.username])
        table.add_row(['tenant_name', self.tenant_name])
        table.add_row(['auth_url', self.auth_url])
        table.add_row(['password', self.password])
        table.add_row(['tenant_id', self.tenant_id])
        table.add_row(['region_name', self.region_name])
        table.add_row(['endpoint', self.endpoint])
        return table.__str__()

    def is_valid(self):
        if self.reason():
            return False
        return True

    def reason(self):
        missing = []
        for attr in ['username', 'password', 'tenant_name', 'region_name']:
            if not self.__getattribute__(attr):
                missing.append(attr)
        if missing:
            return 'missing {0}'.format(', '.join(missing))
        return ''


def get_args(choices):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        'action', action='store', default=None, choices=choices, help='')
    arg_parser.add_argument(
        '--debug', action='store_true',
        help='Prints debugging output onto the console, this may include '
             'OS environment variables, request and response calls. '
             'Helpful for debugging and understanding the API calls.',
        dest='debug', default=False)
    arg_parser.add_argument(
        '-j', '--job', action='store',
        help=('name or ID of the job'),
        dest='job_id', default=None)
    arg_parser.add_argument(
        '-s', '--session', action='store',
        help=('name or ID of the session'),
        dest='session_id', default=None)
    arg_parser.add_argument(
        '--file', action='store',
        help=('Local file that contains the resource '
              'to be uploaded/downloaded'),
        dest='fname', default=None)
    arg_parser.add_argument(
        '--os-endpoint', action='store',
        help=('Specify an endpoint to use instead of retrieving '
              'one from the service catalog (via authentication). '
              'Defaults to env[OS_SERVICE_ENDPOINT]'),
        dest='os_endpoint', default=None)
    arg_parser.add_argument(
        '--os-username', action='store',
        help=('Name used for authentication with the OpenStack '
              'Identity service. Defaults to env[OS_USERNAME].'),
        dest='os_username', default=None)
    arg_parser.add_argument(
        '--os-password', action='store',
        help=('Password used for authentication with the OpenStack '
              'Identity service. Defaults to env[OS_PASSWORD].'),
        dest='os_password', default=None)
    arg_parser.add_argument(
        '--os-tenant-name', action='store',
        help=('Tenant to request authorization on. Defaults to '
              'env[OS_TENANT_NAME].'),
        dest='os_tenant_name', default=None)
    arg_parser.add_argument(
        '--os-tenant-id', action='store',
        help=('Tenant to request authorization on. Defaults to '
              'env[OS_TENANT_ID].'),
        dest='os_tenant_id', default=None)
    arg_parser.add_argument(
        '--os-auth-url', action='store',
        help=('Specify the Identity endpoint to use for '
              'authentication. Defaults to env[OS_AUTH_URL].'),
        dest='os_auth_url', default=None)
    arg_parser.add_argument(
        '--os-region-name', action='store',
        help=('Specify the region to use. Defaults to '
              'env[OS_REGION_NAME].'),
        dest='os_region_name', default=None)
    arg_parser.add_argument(
        '--os-token', action='store',
        help=('Specify an existing token to use instead of retrieving'
              ' one via authentication (e.g. with username & password). '
              'Defaults to env[OS_SERVICE_TOKEN].'),
        dest='os_token', default=None)
    arg_parser.add_argument(
        '-c', '--client-id', action='store',
        help=('Specifies the client_id used when contacting the service.'
              'If not specified it will be automatically created'
              'using the tenant-id and the machine hostname.'),
        dest='client_id', default=None)

    arg_parser.add_argument(
        '-n', '--no-api', action='store_true',
        help='Prevents the scheduler from using the api service',
        dest='no_api', default=False)
    arg_parser.add_argument(
        '-a', '--active-only', action='store_true',
        help='Filter only active jobs/session',
        dest='active_only', default=False)
    arg_parser.add_argument(
        '-d', '--dir', action='store',
        help=('Used to store/retrieve files on local storage, including '
              'those exchanged with the api service. '
              'Default value is {0}'.format(SCHEDULER_CONF_D)),
        dest='jobs_dir', default=SCHEDULER_CONF_D)
    arg_parser.add_argument(
        '-i', '--interval', action='store',
        help=('Specifies the api-polling interval in seconds.'
              'Defaults to 60 seconds'),
        dest='interval', default=60)

    arg_parser.add_argument(
        '-l', '--log-file', action='store',
        help=('location of log file'),
        dest='log_file', default=None)
    return arg_parser.parse_args()
