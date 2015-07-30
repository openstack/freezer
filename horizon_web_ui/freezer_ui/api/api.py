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

import warnings

from django.conf import settings

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa


import freezer.apiclient.client
from horizon_web_ui.freezer_ui.utils import Action
from horizon_web_ui.freezer_ui.utils import ActionJob
from horizon_web_ui.freezer_ui.utils import Backup
from horizon_web_ui.freezer_ui.utils import Client
from horizon_web_ui.freezer_ui.utils import Job
from horizon_web_ui.freezer_ui.utils import JobList
from horizon_web_ui.freezer_ui.utils import Session
from horizon_web_ui.freezer_ui.utils import create_dict_action
from horizon_web_ui.freezer_ui.utils import create_dummy_id


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
        if c['name'] == 'freezer':
            for e in c['endpoints']:
                url = e['publicURL']
        else:
            warnings.warn('Using hardcoded FREEZER_API_URL at {0}'
                          .format(settings.FREEZER_API_URL))
            return getattr(settings, 'FREEZER_API_URL', None)

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

    schedule = {}
    if job['schedule_end_date']:
        schedule['schedule_end_date'] = job.pop('schedule_end_date')

    if job['schedule_interval']:
        schedule['schedule_interval'] = job.pop('schedule_interval')

    if job['schedule_start_date']:
        schedule['schedule_start_date'] = job.pop('schedule_start_date')

    job.pop('clients', None)
    client_id = job.pop('client_id', None)
    actions = job.pop('job_actions', [])

    job['description'] = job.pop('description', None)
    job['job_schedule'] = schedule
    job['job_actions'] = actions
    job['client_id'] = client_id
    return _freezerclient(request).jobs.create(job)


def job_edit(request, context):
    """Edit an existing job file, but leave the actions to actions_edit"""
    job = create_dict_action(**context)

    schedule = {}
    if job['schedule_end_date']:
        schedule['schedule_end_date'] = job.pop('schedule_end_date')

    if job['schedule_interval']:
        schedule['schedule_interval'] = job.pop('schedule_interval')

    if job['schedule_start_date']:
        schedule['schedule_start_date'] = job.pop('schedule_start_date')

    job['description'] = job.pop('description', None)
    actions = job.pop('job_actions', [])

    job.pop('clients', None)
    job.pop('client_id', None)

    job['job_schedule'] = schedule
    job['job_actions'] = actions
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
    job_list = []
    for j in jobs:
        description = j['description']
        job_id = j['job_id']
        try:
            result = j['job_schedule']['result']
        except KeyError:
            result = 'pending'
        job_list.append(JobList(description, result, job_id))
    return job_list


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


def action_list_json(request):
    return _freezerclient(request).actions.list()


def actions_in_job_json(request, job_id):
    job = _freezerclient(request).jobs.get(job_id)
    action_list = []
    for action in job['job_actions']:
        a = {
            "action_id": action['action_id'],
            "freezer_action": action['freezer_action']
        }
        action_list.append(a)
    return action_list


def actions_in_job(request, job_id):
    actions = []
    try:
        job = _freezerclient(request).jobs.get(job_id)
        for a in job['job_actions']:
            try:
                action_id = a['action_id']
            except (KeyError, TypeError):
                action_id = create_dummy_id()

            try:
                action = a['freezer_action']['action']
            except (KeyError, TypeError):
                action = "backup"

            try:
                backup_name = a['freezer_action']['backup_name']
            except (KeyError, TypeError):
                backup_name = "NO BACKUP NAME AVAILABLE"

            actions.append(ActionJob(job_id, action_id, action, backup_name))
    except TypeError:
        pass

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


def client_list_json(request):
    """Return a list of clients directly form the api in json format"""
    clients = _freezerclient(request).registration.list()
    return clients


def client_get(request, client_id):
    """Get a single client"""
    client = _freezerclient(request).registration.get(client_id)
    client = Client(client['uuid'], client['client']['hostname'])
    return client


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


def backups_list(request, offset=0, time_after=None, time_before=None,
                 text_match=None):
    """List all backups and optionally you can provide filters and pagination
     values """
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
    """Get a single backup"""
    backup = _freezerclient(request).backups.get(backup_id)
    backup = Backup(backup)
    return backup
