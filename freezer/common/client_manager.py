"""
(c) Copyright 2016 Hewlett-Packard Development Enterprise, L.P.

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

from freezer.openstack import osclients
from freezer.utils import config
from oslo_config import cfg
from oslo_log import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def parse_osrc(file_name):
    with open(file_name, 'r') as osrc_file:
        return config.osrc_parse(osrc_file.read())


def get_client_manager(backup_args):
    if "osrc" in backup_args:
        options = osclients.OpenstackOpts.create_from_dict(
            parse_osrc(backup_args['osrc']))
    else:
        options = osclients.OpenstackOpts.create_from_env().get_opts_dicts()
    if backup_args['project_id']:
        options['project_name'] = None
        options['project_id'] = backup_args['project_id']
    client_manager = osclients.OSClientManager(
        auth_url=options.pop('auth_url', None),
        auth_method=options.pop('auth_method', 'password'),
        dry_run=backup_args.get('dry_run', None),
        **options
    )
    return client_manager
