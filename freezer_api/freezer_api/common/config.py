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


common_cli_opts = [
    cfg.BoolOpt('verbose',
                short='v',
                default=False,
                help='Print more verbose output.'),
    cfg.BoolOpt('debug',
                short='d',
                default=False,
                help='Print debugging output.'),
]

CONF = cfg.CONF
CONF.register_cli_opts(common_cli_opts)


def parse_args(args=[], usage=None, default_config_files=[]):
    CONF(args=args,
         project='freezer',
         default_config_files=default_config_files)
