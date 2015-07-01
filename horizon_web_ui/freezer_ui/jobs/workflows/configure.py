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

from django.utils.translation import ugettext_lazy as _
import datetime
from horizon import exceptions
from horizon import forms
from horizon import workflows

import horizon_web_ui.freezer_ui.api.api as freezer_api


class ClientsConfigurationAction(workflows.Action):

    client_id = forms.ChoiceField(
        help_text=_("Set the client for this job"),
        required=True)

    def populate_client_id_choices(self, request, context):
        clients = []
        try:
            clients = freezer_api.client_list(request)
        except Exception:
            exceptions.handle(request, _('Error getting client list'))

        client_id = [(c.client_id, c.hostname) for c in clients]
        client_id.insert(0, ('', _('Select A Client')))
        return client_id

    class Meta(object):
        name = _("Clients")
        slug = "clients"


class ClientsConfiguration(workflows.Step):
    action_class = ClientsConfigurationAction
    contributes = ('client_id',)


class ActionsConfigurationAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(ActionsConfigurationAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)

        original_name = args[0].get('original_name', None)

        err_msg = _('Unable to retrieve list of actions.')

        if original_name:
            default_role_field_name = self.get_default_role_field_name()
            self.fields[default_role_field_name] = \
                forms.CharField(required=False,
                                widget=forms.HiddenInput())
            self.fields[default_role_field_name].initial = 'member'

            actions = self.get_member_field_name('member')
            self.fields[actions] = \
                forms.MultipleChoiceField(required=False,
                                          widget=forms.HiddenInput())
        else:
            default_role_field_name = self.get_default_role_field_name()
            self.fields[default_role_field_name] = \
                forms.CharField(required=False)
            self.fields[default_role_field_name].initial = 'member'

            actions = self.get_member_field_name('member')
            self.fields[actions] = forms.MultipleChoiceField(required=False)

        all_actions = []
        try:
            all_actions = freezer_api.action_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        all_actions = [(a.action_id, a.freezer_action['backup_name'])
                       for a in all_actions]

        self.fields[actions].choices = all_actions

        initial_actions = []

        if request.method == 'POST':
            return

        try:
            if original_name:
                configured_actions = \
                    freezer_api.actions_in_job(request, original_name)
                initial_actions = [a.action_id for a in configured_actions]
        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[actions].initial = initial_actions

    class Meta(object):
        name = _("Actions")
        slug = "selected_actions"
        help_text_template = "freezer_ui/jobs" \
                             "/_actions.html"


class ActionsConfiguration(workflows.UpdateMembersStep):
    action_class = ActionsConfigurationAction
    help_text = _(
        "Select the clients that will be backed up using this configuration.")
    available_list_title = _("All Actions")
    members_list_title = _("Selected Actions")
    no_available_text = _("No actions found.")
    no_members_text = _("No actions selected.")
    show_roles = False
    contributes = ("actions",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['actions'] = data.get(member_field_name, [])
        return context


class SchedulingConfigurationAction(workflows.Action):
    start_datetime = forms.CharField(
        label=_("Start Date and Time"),
        required=False,
        help_text=_(""))

    interval = forms.CharField(
        label=_("Interval"),
        required=False,
        help_text=_("Repeat this configuration in a minutes interval."))

    end_datetime = forms.CharField(
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
                self._validate_iso_format(cleaned_data.get('start_datetime')):
            msg = _("Start date time is not in ISO format.")
            self._errors['start_datetime'] = self.error_class([msg])

    def _check_end_datetime(self, cleaned_data):
        if cleaned_data.get('end_datetime') and not \
                self._validate_iso_format(cleaned_data.get('end_datetime')):
            msg = _("End date time is not in ISO format.")
            self._errors['end_datetime'] = self.error_class([msg])

    class Meta(object):
        name = _("Scheduling")
        slug = "scheduling"
        help_text_template = "freezer_ui/jobs" \
                             "/_scheduling.html"


class SchedulingConfiguration(workflows.Step):
    action_class = SchedulingConfigurationAction
    contributes = ('start_datetime',
                   'interval',
                   'end_datetime')


class InfoConfigurationAction(workflows.Action):
    description = forms.CharField(
        label=_("Job Name"),
        help_text=_("Set a short description for this job"),
        required=True)

    original_name = forms.CharField(
        widget=forms.HiddenInput(),
        required=False)

    class Meta(object):
        name = _("Job Info")
        slug = "info"


class InfoConfiguration(workflows.Step):
    action_class = InfoConfigurationAction
    contributes = ('description',
                   'original_name')


class ConfigureJob(workflows.Workflow):
    slug = "job"
    name = _("Job Configuration")
    finalize_button_name = _("Save")
    success_message = _('Job file saved correctly.')
    failure_message = _('Unable to save job file.')
    success_url = "horizon:freezer_ui:jobs:index"
    default_steps = (InfoConfiguration,
                     ClientsConfiguration,
                     SchedulingConfiguration)

    def handle(self, request, context):
        try:
            if context['original_name'] == '':
                return freezer_api.job_create(request, context)
            else:
                return freezer_api.job_edit(request, context)
        except Exception:
            exceptions.handle(request)
            return False
