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


from oslo.config import cfg
import logging


logging_cli_opts = [
    cfg.StrOpt('log-file',
               metavar='PATH',
               help='(Optional) Name of log file to output to. '
                    'If no default is set, logging will go to stdout.'),
    cfg.BoolOpt('use-syslog',
                help='Use syslog for logging.'),
    cfg.StrOpt('syslog-log-facility',
               help='syslog facility to receive log lines')
]

logging_opts = [
    cfg.StrOpt('logging_file',
               metavar='PATH',
               default='freezer-api.log',
               help='(Optional) Name of log file to output to. '
                    'If no default is set, logging will go to stdout.'),
    cfg.BoolOpt('logging_use_syslog',
                default=False,
                help='Use syslog for logging.'),
    cfg.StrOpt('logging_syslog_log_facility',
               default='LOG_USER',
               help='syslog facility to receive log lines')
]


CONF = cfg.CONF
CONF.register_opts(logging_opts)
CONF.register_cli_opts(logging_cli_opts)


def setup():
    try:
        log_file = CONF['log-file']         # cli provided
    except:
        log_file = CONF['logging_file']     # .conf file
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s %(message)s')
