# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

"""Some helper functions to use the freezer_ui client functionality
   from horizon.
"""

from django.conf import settings
import warnings
import freezer.apiclient.client

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa


class Dict2Object(object):
    """Makes dictionary fields accessible as if they are attributes.

    The dictionary keys become class attributes. It is possible to use one
    nested dictionary by overwriting nested_dict with the key of that nested
    dict.

    This class is needed because we mostly deal with objects in horizon (e.g.
    for providing data to the tables) but the api only gives us json data.
    """
    nested_dict = None

    def __init__(self, data_dict):
        self.data_dict = data_dict

    def __getattr__(self, attr):
        """Make data_dict fields available via class interface """
        if attr in self.data_dict:
            return self.data_dict[attr]
        elif attr in self.data_dict[self.nested_dict]:
            return self.data_dict[self.nested_dict][attr]
        else:
            return object.__getattribute__(self, attr)

    def get_dict(self):
        return self.data_dict


class Action(Dict2Object):
    nested_dict = 'job'

    @property
    def id(self):
        return self.action_id


class Configuration(Dict2Object):
    nested_dict = 'config_file'

    @property
    def id(self):
        return self.config_id


class Backup(Dict2Object):
    nested_dict = 'backup_metadata'

    @property
    def id(self):
        return self.backup_id


class Client(Dict2Object):
    nested_dict = 'client'

    @property
    def id(self):
        return self.client_id

    @property
    def name(self):
        return self.client_id


class ConfigClient(object):

    def __init__(self, name, last_backup):
        self.id = name
        self.name = name
        self.last_backup = last_backup


@memoized
def get_service_url(request):
    """ Get Freezer API url from keystone catalog.
    if Freezer is not set in keystone, the fallback will be
    'FREEZER_API_URL' in local_settings.py
    """
    url = None

    catalog = (getattr(request.user, "service_catalog", None))
    if not catalog:
        warnings.warn('Using hardcoded FREEZER_API_URL at {0}'
                      .format(settings.FREEZER_API_URL))
        return getattr(settings, 'FREEZER_API_URL', None)

    for c in catalog:
        if c['name'] == 'Freezer':
            for e in c['endpoints']:
                url = e['publicURL']
    return url


@memoized
def _freezerclient(request):
    api_url = get_service_url(request)

    return freezer.apiclient.client.Client(
        token=request.user.token.id,
        auth_url=getattr(settings, 'OPENSTACK_KEYSTONE_URL'),
        endpoint=api_url)


def configuration_create(request, name=None, container_name=None,
                         src_file=None, levels=None, optimize=None,
                         compression=None, encryption_password=None,
                         clients=[], start_datetime=None, interval=None,
                         exclude=None, log_file=None, proxy=None,
                         max_priority=False):
    """Create a new configuration file """

    data = {
        "name": name,
        "container_name": container_name,
        "src_file": src_file,
        "levels": levels,
        "optimize": optimize,
        "compression": compression,
        "encryption_password": encryption_password,
        "clients": clients,
        "start_datetime": start_datetime,
        "interval": interval,
        "exclude": exclude,
        "log_file": log_file,
        "proxy": proxy,
        "max_priority": max_priority
    }
    return _freezerclient(request).configs.create(data)


def configuration_update(request, config_id=None, name=None,
                         src_file=None, levels=None, optimize=None,
                         compression=None, encryption_password=None,
                         clients=[], start_datetime=None, interval=None,
                         exclude=None, log_file=None, proxy=None,
                         max_priority=False, container_name=None,):

    """Update a new configuration file """
    data = {
        "name": name,
        "container_name": container_name,
        "src_file": src_file,
        "levels": levels,
        "optimize": optimize,
        "compression": compression,
        "encryption_password": encryption_password,
        "clients": clients,
        "start_datetime": start_datetime,
        "interval": interval,
        "exclude": exclude,
        "log_file": log_file,
        "proxy": proxy,
        "max_priority": max_priority
    }
    return _freezerclient(request).configs.update(config_id, data)


def configuration_delete(request, obj_id):
    return _freezerclient(request).configs.delete(obj_id)


def configuration_clone(request, config_id):
    config_file = _freezerclient(request).configs.get(config_id)
    data = config_file[0]['config_file']
    data['name'] = '{0}_clone'.format(data['name'])
    return _freezerclient(request).configs.create(data)


def configuration_get(request, config_id):
    config_file = _freezerclient(request).configs.get(config_id)
    if config_file:
        return [Configuration(data) for data in config_file]
    return []


def configuration_list(request):
    configurations = _freezerclient(request).configs.list()
    configurations = [Configuration(data) for data in configurations]
    return configurations


def clients_in_config(request, config_id):
    configuration = configuration_get(request, config_id)
    clients = []
    last_backup = None
    clients_dict = [c.get_dict() for c in configuration]
    for client in clients_dict:
        for client_id in client['config_file']['clients']:
            backups, has_more = backups_list(request, text_match=client_id)
            backups = [Backup(data) for data in backups]
            backups = [b.get_dict() for b in backups]
            for backup in backups:
                last_backup = backup.data_dict['backup_metadata']['timestamp']
            clients.append(ConfigClient(client_id, last_backup))
    return clients


def client_list(request, limit=20):
    clients = _freezerclient(request).registration.list(limit=limit)
    clients = [Client(client) for client in clients]
    return clients


def backups_list(request, offset=0, time_after=None, time_before=None,
                 text_match=None):
    page_size = utils.get_page_size(request)

    search = {}

    if time_after:
        search['time_after'] = time_after
    if time_before:
        search['time_before'] = time_before

    if text_match:
        search['match'] = [
            {
                "_all": text_match,
            }
        ]

    backups = _freezerclient(request).backups.list(
        limit=page_size + 1,
        offset=offset,
        search=search)

    if len(backups) > page_size:
        backups.pop()
        has_more = True
    else:
        has_more = False

    # Wrap data in object for easier handling
    backups = [Backup(data) for data in backups]

    return backups, has_more


def backup_get(request, backup_id):
    data = _freezerclient(request).backups.get(backup_id)
    if data:
        return Backup(data[0])


def restore_action_create(request,
                          backup_id,
                          destination_client_id,
                          destination_path,
                          description=None,
                          dry_run=False,
                          max_prio=False):
    c = _freezerclient(request)
    backup = c.backups.get(backup_id)[0]

    action = {
        "job": {
            "action": "restore",
            "container_name": backup['backup_metadata']['container'],
            "restore-abs-path": destination_path,
            "backup-name": backup['backup_metadata']['backup_name'],
            "restore-from-host": backup['backup_metadata']['host_name'],
            "max_cpu_priority": max_prio,
            "dry_run": dry_run
        },
        "description": description,
        "client_id": destination_client_id
    }

    c.actions.create(action)


def actions_list(request, offset=0):
    page_size = utils.get_page_size(request)

    actions = _freezerclient(request).actions.list(
        limit=page_size + 1,
        offset=offset)

    if len(actions) > page_size:
        actions.pop()
        has_more = True
    else:
        has_more = False

    # Wrap data in object for easier handling
    actions = [Action(data['action']) for data in actions]

    return actions, has_more
