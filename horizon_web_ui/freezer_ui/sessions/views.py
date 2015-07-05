# Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed `under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import browsers
from horizon import exceptions
from horizon import workflows

import horizon_web_ui.freezer_ui.sessions.browsers as project_browsers
from horizon_web_ui.freezer_ui.sessions.workflows import attach
from horizon_web_ui.freezer_ui.sessions.workflows import create_session
import horizon_web_ui.freezer_ui.api.api as freezer_api
from horizon_web_ui.freezer_ui.utils import SessionJob


class AttachToSessionWorkflow(workflows.WorkflowView):
    workflow_class = attach.AttachJobToSession

    def get_object(self, *args, **kwargs):
        job_id = self.kwargs['job_id']
        try:
            return freezer_api.job_get(self.request, job_id)
        except Exception:
            redirect = reverse("horizon:freezer_ui:jobs:index")
            msg = _('Unable to retrieve details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def is_update(self):
        return 'job_id' in self.kwargs and \
               bool(self.kwargs['job_id'])

    def get_initial(self):
        initial = super(AttachToSessionWorkflow, self).get_initial()
        job = self.get_object()[0]
        initial.update({'job_id': job.id})
        return initial


class SessionsView(browsers.ResourceBrowserView):
    browser_class = project_browsers.SessionBrowser
    template_name = "freezer_ui/sessions/browser.html"

    def get_sessions_data(self):
        sessions = []
        try:
            sessions = freezer_api.session_list(self.request)
        except Exception:
            msg = _('Unable to retrieve sessions list.')
            exceptions.handle(self.request, msg)
        return sessions

    def get_jobs_data(self):
        jobs = []
        session = None
        try:
            if self.kwargs['session_id']:
                session = freezer_api.session_get(
                    self.request,
                    self.kwargs['session_id'])

            try:
                jobs = [SessionJob(k,
                                   self.kwargs['session_id'],
                                   v['client_id'],
                                   v['status'])
                        for k, v in session.jobs.iteritems()]
            except AttributeError:
                pass
        except Exception:
            msg = _('Unable to retrieve session information.')
            exceptions.handle(self.request, msg)
        return jobs


class CreateSessionWorkflow(workflows.WorkflowView):
    workflow_class = create_session.CreateSession

    def get_object(self, *args, **kwargs):
        session_id = self.kwargs['session_id']
        try:
            return freezer_api.session_get(self.request, session_id)
        except Exception:
            redirect = reverse("horizon:freezer_ui:sessions:index")
            msg = _('Unable to retrieve session.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(CreateSessionWorkflow, self).get_initial()
        if self.is_update():
            session = self.get_object()
            initial.update({
                'description': session.description,
                'session_id': session.session_id,
                'start_datetime': session.start_datetime,
                'interval': session.interval,
                'end_datetime': session.end_datetime
            })
        return initial

    def is_update(self):
        return 'session_id' in self.kwargs and \
               bool(self.kwargs['session_id'])
