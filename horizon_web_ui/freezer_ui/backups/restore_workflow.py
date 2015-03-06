# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
#    under the License.

import logging

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import workflows

import horizon_web_ui.freezer_ui.api.api as freezer_api

LOG = logging.getLogger(__name__)


class DestinationAction(workflows.MembershipAction):
    path = forms.CharField(label=_("Destination Path"),
                           initial='/home/',
                           help_text="The path in which the backup should be "
                                     "restored",
                           required=True)
    backup_id = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        if 'client' in self.request.POST:
            self.cleaned_data['client'] = self.request.POST['client']
        else:
            raise ValidationError('Client is required')

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


class OptionsAction(workflows.Action):
    description = forms.CharField(widget=forms.Textarea,
                                  label="Description",
                                  required=False,
                                  help_text="Free text description of this "
                                            "restore.")

    dry_run = forms.BooleanField(label=_("Dry Run"),
                                 required=False)
    max_prio = forms.BooleanField(label=_("Max Process Priority"),
                                  required=False)

    class Meta(object):
        name = _("Options")


class Options(workflows.Step):
    action_class = OptionsAction
    contributes = ('description', 'dry_run', 'max_prio')
    after = Destination


class ConfigureBackups(workflows.Workflow):
    slug = "restore"
    name = _("Restore")
    success_url = "horizon:freezer_ui:backups:index"
    success_message = "Restore job successfully queued. It will get " \
                      "executed soon."
    wizard = False
    default_steps = (Destination, Options)

    def __init__(self, *args, **kwargs):
        super(ConfigureBackups, self).__init__(*args, **kwargs)
        pass

    def handle(self, request, data):
        freezer_api.restore_action_create(
            request,
            backup_id=data['backup_id'],
            destination_client_id=data['client'],
            destination_path=data['path'],
            description=data['description'],
            dry_run=data['dry_run'],
            max_prio=data['max_prio']
        )
        return True
