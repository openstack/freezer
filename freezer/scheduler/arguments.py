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

import argparse
import os

from freezer.apiclient import client as api_client

DEFAULT_FREEZER_SCHEDULER_CONF_D = '/etc/freezer/scheduler/conf.d'


def base_parser(parser):
    scheduler_conf_d = os.environ.get('FREEZER_SCHEDULER_CONF_D',
                                      DEFAULT_FREEZER_SCHEDULER_CONF_D)
    parser.add_argument(
        '-j', '--job', action='store',
        help=('name or ID of the job'),
        dest='job_id', default=None)
    parser.add_argument(
        '-s', '--session', action='store',
        help=('name or ID of the session'),
        dest='session_id', default=None)
    parser.add_argument(
        '--file', action='store',
        help=('Local file that contains the resource '
              'to be uploaded/downloaded'),
        dest='fname', default=None)
    parser.add_argument(
        '-c', '--client-id', action='store',
        help=('Specifies the client_id used when contacting the service.'
              'If not specified it will be automatically created'
              'using the tenant-id and the machine hostname.'),
        dest='client_id', default=None)
    parser.add_argument(
        '-n', '--no-api', action='store_true',
        help='Prevents the scheduler from using the api service',
        dest='no_api', default=False)
    parser.add_argument(
        '-a', '--active-only', action='store_true',
        help='Filter only active jobs/session',
        dest='active_only', default=False)
    parser.add_argument(
        '-f', '--conf', action='store',
        help=('Used to store/retrieve files on local storage, including '
              'those exchanged with the api service. '
              'Default value is {0} '
              '(Env: FREEZER_SCHEDULER_CONF_D)'.format(scheduler_conf_d)),
        dest='jobs_dir', default=scheduler_conf_d)
    parser.add_argument(
        '-i', '--interval', action='store',
        help=('Specifies the api-polling interval in seconds.'
              'Defaults to 60 seconds'),
        dest='interval', default=60)

    parser.add_argument(
        '-v', '--verbose',
        action='count',
        dest='verbose_level',
        default=1,
        help='Increase verbosity of output. Can be repeated.',
    )
    parser.add_argument(
        '--debug',
        default=False,
        action='store_true',
        help='show tracebacks on errors',
    )
    parser.add_argument(
        '--no-daemon',
        action='store_true',
        help='Prevents the scheduler from running in daemon mode',
        dest='no_daemon', default=False
    )
    parser.add_argument(
        '-l', '--log-file', action='store',
        help=('location of log file'),
        dest='log_file', default=None)

    return parser


def get_args(choices):
    parser = base_parser(
        api_client.build_os_option_parser(
            argparse.ArgumentParser(description='Freezer Scheduler')
        ))
    parser.add_argument(
        'action', action='store', default=None, choices=choices, help='')
    return parser.parse_args()
