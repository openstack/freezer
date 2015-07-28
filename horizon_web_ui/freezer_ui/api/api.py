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


class Client(object):
    def __init__(self, client, hostname):
        self.client = client
        self.hostname = hostname


class ActionJob(object):
    def __init__(self, job_id, action_id, action, backup_name):
        self.job_id = job_id
        self.action_id = action_id
        self.action = action
        self.backup_name = backup_name


class Session(object):
    def __init__(self, session_id, description, status, jobs,
                 start_datetime, interval, end_datetime):
        self.session_id = session_id
        self.description = description
        self.status = status
        self.jobs = jobs
        self.start_datetime = start_datetime
        self.interval = interval
        self.end_datetime = end_datetime


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
    client_id = job.pop('client_id', None)
    job['description'] = job.pop('description', None)

    schedule = {
        'schedule_end_date': job.pop('schedule_end_date', None),
        'schedule_interval': job.pop('schedule_interval', None),
        'schedule_start_date': job.pop('schedule_start_date', None),
    }
    job['job_schedule'] = schedule
    job['job_actions'] = []
    job['client_id'] = client_id
    return _freezerclient(request).jobs.create(job)


def job_edit(request, context):
    """Edit an existing job file, but leave the actions to actions_edit"""
    job = create_dict_action(**context)
    job['description'] = job.pop('description', None)
    job['client_id'] = job.pop('client_id', None)
    schedule = {
        'schedule_end_date': job.pop('schedule_end_date', None),
        'schedule_interval': job.pop('schedule_interval', None),
        'schedule_start_date': job.pop('schedule_start_date', None),
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
    clients = [Client(c['uuid'], c['client']['hostname'])
               for c in clients]
    return clients


def add_job_to_session(request, session_id, job_id):
    """This function will add a job to a session and the API will handle the
    copy of job information to the session """
    try:
        return _freezerclient(request).sessions.add_job(session_id, job_id)
    except Exception:
        return False


def remove_job_from_session(request, session_id, job_id):
    """Remove a job from a session will delete the job information but not the
    job itself """
    try:
        return _freezerclient(request).sessions.remove_job(session_id, job_id)
    except Exception:
        return False


def session_create(request, context):
    """A session is a group of jobs who share the same scheduling time. """
    session = create_dict_action(**context)
    session['description'] = session.pop('description', None)
    schedule = {
        'schedule_end_date': session.pop('schedule_end_date', None),
        'schedule_interval': session.pop('schedule_interval', None),
        'schedule_start_date': session.pop('schedule_start_date', None),
    }
    session['schedule'] = schedule
    return _freezerclient(request).sessions.create(session)


def session_update(request, context):
    """Update session information """
    session = create_dict_action(**context)
    session_id = session.pop('session_id', None)
    session['description'] = session.pop('description', None)
    schedule = {
        'schedule_end_date': session.pop('schedule_end_date', None),
        'schedule_interval': session.pop('schedule_interval', None),
        'schedule_start_date': session.pop('schedule_start_date', None),
    }
    session['schedule'] = schedule
    return _freezerclient(request).sessions.update(session_id, session)


def session_delete(request, session_id):
    """Delete session from API """
    return _freezerclient(request).sessions.delete(session_id)


def session_list(request):
    """List all sessions """
    sessions = _freezerclient(request).sessions.list_all()
    sessions = [Session(s['session_id'],
                        s['description'],
                        s['status'],
                        s['jobs'],
                        s['schedule']['schedule_start_date'],
                        s['schedule']['schedule_interval'],
                        s['schedule']['schedule_end_date'])
                for s in sessions]
    return sessions


def session_get(request, session_id):
    """Get a single session """
    session = _freezerclient(request).sessions.get(session_id)
    session = Session(session['session_id'],
                      session['description'],
                      session['status'],
                      session['jobs'],
                      session['schedule']['schedule_start_date'],
                      session['schedule']['schedule_interval'],
                      session['schedule']['schedule_end_date'])
    return session
