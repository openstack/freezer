# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import exceptions
from horizon import workflows

import horizon_web_ui.freezer_ui.api.api as freezer_api


class DestinationAction(workflows.MembershipAction):
    path = forms.CharField(label=_("Destination Path"),
                           help_text=_("The path in which the backup should be "
                                       "restored"),
                           required=True)
    backup_id = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        if 'client' in self.request.POST:
            self.cleaned_data['client'] = self.request.POST['client']
        else:
            raise ValidationError(_('Client is required'))

        return self.cleaned_data

    class Meta(object):
        name = _("Destination")
        slug = "destination"


class Destination(workflows.Step):
    template_name = 'freezer_ui/backups/restore.html'
    action_class = DestinationAction
    contributes = ('client', 'path', 'backup_id')

    def has_required_fields(self):
        return True


class Restore(workflows.Workflow):
    slug = "restore"
    name = _("Restore")
    finalize_button_name = _("Restore")
    success_url = "horizon:freezer_ui:backups:index"
    success_message = _("Restore job successfully queued. It will get "
                        "executed soon.")
    wizard = False
    default_steps = (Destination,)

    def handle(self, request, data):
        try:
            backup_id = data['backup_id']
            client_id = data['client']
            client = freezer_api.client_get(request, client_id)
            backup = freezer_api.backup_get(request, backup_id)
            name = "Restore job for {0}".format(client_id)

            # 1st step is to create a job
            restore_job = {
                "description": name,
                "client_id": client_id,
                "schedule_end_date": None,
                "schedule_interval": None,
                "schedule_start_date": None
            }
            job = freezer_api.job_create(request, restore_job)

            # 2nd step is to create an action for this job
            restore_action = {
                "original_name": job,  # this is the job_id
                "action": "restore",
                "backup_name":
                    backup.data_dict[0]['backup_metadata']['backup_name'],
                "restore_abs_path": data['path'],
                "container":
                    backup.data_dict[0]['backup_metadata']['container'],
                "restore_from_host": client.hostname,
                "max_retries": 3,
                "max_retries_interval": 60,
                "mandatory": False
            }
            return freezer_api.action_create(request, restore_action)
        except Exception:
            exceptions.handle(request)
            return False
