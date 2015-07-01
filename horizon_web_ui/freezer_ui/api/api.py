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
from horizon_web_ui.freezer_ui.utils import create_dict_action

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
    nested_dict = 'job_action'

    @property
    def id(self):
        return self.job_id


class Job(Dict2Object):
    nested_dict = 'job_actions'

    @property
    def id(self):
        return self.job_id


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


class ActionJob(object):
    def __init__(self, job_id, action_id, action, backup_name):
        self.job_id = job_id
        self.action_id = action_id
        self.action = action
        self.backup_name = backup_name


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


def job_create(request, context):
    """Create a new job file """
    job = create_dict_action(**context)
    job['description'] = job.pop('description', None)
    job['client_id'] = job.pop('client_id', None)
    schedule = {
        'end_datetime': job.pop('end_datetime', None),
        'interval': job.pop('interval', None),
        'start_datetime': job.pop('start_datetime', None),
    }
    job['job_schedule'] = schedule
    job['job_actions'] = []
    return _freezerclient(request).jobs.create(job)


def job_edit(request, context):
    """Edit an existing job file, but leave the actions to actions_edit"""
    job = create_dict_action(**context)
    job['description'] = job.pop('description', None)
    job['client_id'] = job.pop('client_id', None)
    schedule = {
        'end_datetime': job.pop('end_datetime', None),
        'interval': job.pop('interval', None),
        'start_datetime': job.pop('start_datetime', None),
    }
    job['job_schedule'] = schedule
    job_id = job.pop('original_name', None)
    return _freezerclient(request).jobs.update(job_id, job)


def job_delete(request, obj_id):
    return _freezerclient(request).jobs.delete(obj_id)


def job_clone(request, job_id):
    job_file = _freezerclient(request).jobs.get(job_id)
    job_file['description'] = \
        '{0}_clone'.format(job_file['description'])
    job_file.pop('job_id', None)
    job_file.pop('_version', None)
    return _freezerclient(request).jobs.create(job_file)


def job_get(request, job_id):
    job_file = _freezerclient(request).jobs.get(job_id)
    if job_file:
        job_item = [job_file]
        job = [Job(data) for data in job_item]
        return job
    return []


def job_list(request):
    jobs = _freezerclient(request).jobs.list_all()
    jobs = [Job(data) for data in jobs]
    return jobs


def action_create(request, context):
    """Create a new action for a job """
    action = {}

    if context['max_retries']:
        action['max_retries'] = context.pop('max_retries')
    if context['max_retries_interval']:
        action['max_retries_interval'] = context.pop('max_retries_interval')
    if context['mandatory']:
        action['mandatory'] = context.pop('mandatory')

    job_id = context.pop('original_name')
    job_action = create_dict_action(**context)
    action['freezer_action'] = job_action
    action_id = _freezerclient(request).actions.create(action)
    action['action_id'] = action_id
    job = _freezerclient(request).jobs.get(job_id)
    job['job_actions'].append(action)
    return _freezerclient(request).jobs.update(job_id, job)


def action_list(request):
    actions = _freezerclient(request).actions.list()
    actions = [Action(data) for data in actions]
    return actions


def actions_in_job(request, job_id):
    job = _freezerclient(request).jobs.get(job_id)
    actions = []
    try:
        job_id = job['job_id']
        actions = [ActionJob(job_id,
                             action['action_id'],
                             action['freezer_action']['action'],
                             action['freezer_action']['backup_name'])
                   for action in job['job_actions']]
    except Exception:
        warnings.warn('No more actions in your job')
    return actions


def action_get(request, action_id):
    action = _freezerclient(request).actions.get(action_id)
    return action


def action_update(request, context):
    job_id = context.pop('original_name')
    action_id = context.pop('action_id')

    job = _freezerclient(request).jobs.get(job_id)

    for a in job['job_actions']:
        if a['action_id'] == action_id:

            if context['max_retries']:
                a['max_retries'] = context.pop('max_retries')
            if context['max_retries_interval']:
                a['max_retries_interval'] = \
                    context.pop('max_retries_interval')
            if context['mandatory']:
                a['mandatory'] = context.pop('mandatory')

            updated_action = create_dict_action(**context)

            a['freezer_action'].update(updated_action)

    return _freezerclient(request).jobs.update(job_id, job)


def action_delete(request, ids):
    action_id, job_id = ids.split('===')
    job = _freezerclient(request).jobs.get(job_id)
    for action in job['job_actions']:
        if action['action_id'] == action_id:
            job['job_actions'].remove(action)
    return _freezerclient(request).jobs.update(job_id, job)


def client_list(request):
    clients = _freezerclient(request).registration.list()
    clients = [Client(client) for client in clients]
    return clients
