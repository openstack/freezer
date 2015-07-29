# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import datetime

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

import horizon_web_ui.freezer_ui.api.api as freezer_api


class SessionConfigurationAction(workflows.Action):
    description = forms.CharField(
        label=_("Session Name"),
        help_text=_("Define a name for this session"),
        required=True)

    session_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=False)

    class Meta:
        name = _("Session Information")
        slug = "sessions"


class SessionConfiguration(workflows.Step):
    action_class = SessionConfigurationAction
    contributes = ('description',
                   'session_id')


class SchedulingConfigurationAction(workflows.Action):
    schedule_start_date = forms.CharField(
        label=_("Start Date and Time"),
        required=False,
        help_text=_(""))

    schedule_interval = forms.CharField(
        label=_("Interval"),
        required=False,
        help_text=_(""))

    schedule_end_date = forms.CharField(
        label=_("End Date and Time"),
        required=False,
        help_text=_(""))

    def __init__(self, request, context, *args, **kwargs):
        self.request = request
        self.context = context
        super(SchedulingConfigurationAction, self).__init__(
            request, context, *args, **kwargs)

    def clean(self):
        cleaned_data = super(SchedulingConfigurationAction, self).clean()
        self._check_start_datetime(cleaned_data)
        self._check_end_datetime(cleaned_data)
        return cleaned_data

    def _validate_iso_format(self, start_date):
        try:
            return datetime.datetime.strptime(
                start_date, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return False

    def _check_start_datetime(self, cleaned_data):
        if cleaned_data.get('start_datetime') and not \
                self._validate_iso_format(
                    cleaned_data.get('schedule_start_date')):
            msg = _("Start date time is not in ISO format.")
            self._errors['schedule_start_date'] = self.error_class([msg])

    def _check_end_datetime(self, cleaned_data):
        if cleaned_data.get('end_datetime') and not \
                self._validate_iso_format(
                    cleaned_data.get('schedule_end_date')):
            msg = _("End date time is not in ISO format.")
            self._errors['schedule_end_date'] = self.error_class([msg])

    class Meta(object):
        name = _("Scheduling")
        slug = "scheduling"
        help_text_template = "freezer_ui/jobs" \
                             "/_scheduling.html"


class SchedulingConfiguration(workflows.Step):
    action_class = SchedulingConfigurationAction
    contributes = ('schedule_start_date',
                   'schedule_interval',
                   'schedule_end_date')


class CreateSession(workflows.Workflow):
    slug = "create_session"
    name = _("Create Session")
    finalize_button_name = _("Create")
    success_message = _('Session created successfully.')
    failure_message = _('Unable to create session.')
    success_url = "horizon:freezer_ui:sessions:index"
    default_steps = (SessionConfiguration,
                     SchedulingConfiguration)

    def handle(self, request, context):
        try:
            if context['session_id'] == '':
                return freezer_api.session_create(request, context)
            else:
                return freezer_api.session_update(request, context)
        except Exception:
            exceptions.handle(request)
            return False
