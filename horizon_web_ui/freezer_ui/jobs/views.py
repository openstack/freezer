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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from horizon import workflows

from horizon import browsers
from horizon import exceptions
import horizon_web_ui.freezer_ui.api.api as freezer_api
import horizon_web_ui.freezer_ui.jobs.browsers as project_browsers
import workflows.configure as configure_workflow
import workflows.action as action_workflow
from horizon_web_ui.freezer_ui.utils import create_dict_action


class JobWorkflowView(workflows.WorkflowView):
    workflow_class = configure_workflow.ConfigureJob

    def get_object(self, *args, **kwargs):
        job_id = self.kwargs['backup_name']
        try:
            return freezer_api.job_get(self.request, job_id)
        except Exception:
            redirect = reverse("horizon:freezer_ui:jobs:index")
            msg = _('Unable to retrieve details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def is_update(self):
        return 'backup_name' in self.kwargs and \
               bool(self.kwargs['backup_name'])

    def get_initial(self):
        initial = super(JobWorkflowView, self).get_initial()
        if self.is_update():
            initial.update({'original_name': None})
            job = self.get_object()[0]
            d = job.get_dict()
            schedule = create_dict_action(**d['job_schedule'])
            initial.update(**schedule)
            info = {k: v for k, v in d.items()
                    if not k == 'job_schedule'}
            initial.update(**info)
            initial.update({'original_name': d.get('job_id', None)})
        return initial


class JobsView(browsers.ResourceBrowserView):
    browser_class = project_browsers.ContainerBrowser
    template_name = "freezer_ui/jobs/browser.html"

    def get_jobs_data(self):
        jobs = []
        try:
            jobs = freezer_api.job_list(self.request)
        except Exception:
            msg = _('Unable to retrieve job file list.')
            exceptions.handle(self.request, msg)
        return jobs

    def get_status_data(self):
        job = []
        try:
            if self.kwargs['job_id']:
                job = freezer_api.actions_in_job(
                    self.request, self.kwargs['job_id'])
        except Exception:
            msg = _('Unable to retrieve instances for this job.')
            exceptions.handle(self.request, msg)
        return job


class ActionWorkflowView(workflows.WorkflowView):
    workflow_class = action_workflow.ConfigureAction
    success_url = reverse_lazy("horizon:freezer_ui:jobs:index")

    def get_context_data(self, **kwargs):
        context = super(ActionWorkflowView, self).get_context_data(**kwargs)
        job_id = self.kwargs['job_id']
        context['job_id'] = job_id
        return context

    def get_object(self, *args, **kwargs):
        ids = self.kwargs['job_id']
        try:
            action_id, job_id = ids.split('===')
        except ValueError:
            action_id = None
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

    def get_initial(self, **kwargs):
        initial = super(ActionWorkflowView, self).get_initial()
        try:
            action_id, job_id = self.kwargs['job_id'].split('===')
        except ValueError:
            job_id = self.kwargs['job_id']
            action_id = None

        if self.is_update():
            initial.update({'original_name': None})
            job = self.get_object()[0]
            d = job.get_dict()
            for action in d['job_actions']:
                if action['action_id'] == action_id:
                    actions = create_dict_action(**action)
                    rules = {k: v for k, v in action.items()
                             if not k == 'freezer_action'}
                    initial.update(**actions['freezer_action'])
                    initial.update(**rules)
            initial.update({'original_name': job.id})
        return initial

