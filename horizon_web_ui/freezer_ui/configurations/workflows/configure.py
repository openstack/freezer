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
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa
from horizon import exceptions
from horizon import forms
from horizon import workflows

import horizon_web_ui.freezer_ui.api.api as freezer_api

LOG = logging.getLogger(__name__)


class BackupConfigurationAction(workflows.Action):
    original_name = forms.CharField(
        widget=forms.HiddenInput(),
        required=False)

    name = forms.CharField(
        label=_("Configuration Name"),
        required=True)

    container_name = forms.CharField(
        label=_("Swift Container Name"),
        required=True)

    mode = forms.ChoiceField(
        help_text="Choose what you want to backup",
        required=True)

    src_file = forms.CharField(
        label=_("Source File/Directory"),
        help_text="The file or directory you want to back up to Swift",
        required=True)

    def populate_mode_choices(self, request, context):
        return [
            ('fs', _("File system")),
            ('snapshot', _("Snapshot")),
            ('mongo', _("MongoDB")),
            ('mysql', _("MySQL")),
            ('mssql', _("Microsoft SQL Server")),
            ('elastic', _("ElasticSearch")),
            ('postgres', _("Postgres")),
        ]

    class Meta(object):
        name = _("Backup")


class BackupConfiguration(workflows.Step):
    action_class = BackupConfigurationAction
    contributes = ('mode',
                   'name',
                   'container_name',
                   'src_file',
                   'original_name')


class OptionsConfigurationAction(workflows.Action):
    levels = forms.IntegerField(
        label=_("Number of incremental backups"),
        initial=0,
        min_value=0,
        required=False,
        help_text="Set the backup level used with tar"
        " to implement incremental backup. "
        "If a level 1 is specified but no "
        "level 0 is already available, a "
        "level 0 will be done and "
        "subsequently backs to level 1. "
        "Default 0 (No Incremental)")

    optimize = forms.ChoiceField(
        choices=[('speed', _("Speed (tar)")),
                 ('bandwith', "Bandwith/Space (rsync)")],
        help_text="",
        label='Optimize for...',
        required=False)

    compression = forms.ChoiceField(
        choices=[('gzip', _("Minimum Compression (GZip/Zip)")),
                 ('bzip', _("Medium Compression (BZip2")),
                 ('xz', _("Maximum Compression (XZ)"))],
        help_text="",
        label='Compression Level',
        required=False)

    encryption_password = forms.CharField(
        label=_("Encryption Password"),  # encryption key
        widget=forms.PasswordInput(),
        help_text="",
        required=False)

    class Meta(object):
        name = _("Options")


class OptionsConfiguration(workflows.Step):
    action_class = OptionsConfigurationAction
    contributes = ('levels',
                   'optimize',
                   'compression',
                   'encryption_password',)


class ClientsConfigurationAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(ClientsConfigurationAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)

        err_msg_configured = 'Unable to retrieve list of configured clients.'
        err_msg_all = 'Unable to retrieve list of clients.'

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        all_clients = []
        try:
            all_clients = freezer_api.client_list(request)
        except Exception:
            exceptions.handle(request, err_msg_all)

        clients = [(c.client_id, c.name) for c in all_clients]

        self.fields[field_name].choices = clients

        if request.method == 'POST':
            return

        initial_clients = []
        try:
            original_name = args[0].get('original_name', None)
            if original_name:
                configured_clients = \
                    freezer_api.clients_in_config(request, original_name)
                initial_clients = [client.id for client in configured_clients]
        except Exception:
            exceptions.handle(request, err_msg_configured)

        self.fields[field_name].initial = initial_clients

    class Meta(object):
        name = _("Clients")
        slug = "configure_clients"


class ClientsConfiguration(workflows.UpdateMembersStep):
    action_class = ClientsConfigurationAction
    help_text = _(
        "Select the clients that will be backed up using this configuration.")
    available_list_title = _("All Clients")
    members_list_title = _("Selected Clients")
    no_available_text = _("No clients found.")
    no_members_text = _("No clients selected.")
    show_roles = False
    contributes = ("clients",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['clients'] = data.get(member_field_name, [])
        return context


class SchedulingConfigurationAction(workflows.Action):
    start_datetime = forms.CharField(
        label=_("Start Date and Time"),
        required=False,
        help_text=_("Set a start date and time for backups"))

    interval = forms.CharField(
        label=_("Interval"),
        required=False,
        help_text=_("Repeat this configuration in an interval. e.g. 24 hours"))

    class Meta(object):
        name = _("Scheduling")


class SchedulingConfiguration(workflows.Step):
    action_class = SchedulingConfigurationAction
    contributes = ('start_datetime',
                   'interval',)


class AdvancedConfigurationAction(workflows.Action):
    exclude = forms.CharField(
        label=_("Exclude Files"),
        help_text="Exclude files, given as a PATTERN.Ex:"
                  " --exclude '*.log' will exclude any "
                  "file with name ending with .log. "
                  "Default no exclude",
        required=False)
    log_file = forms.CharField(
        label=_("Log File Path"),
        help_text="Set log file. By default logs to "
                  "/var/log/freezer.log If that file "
                  "is not writable, freezer tries to "
                  "log to ~/.freezer/freezer.log",
        required=False)

    proxy = forms.CharField(
        label=_("Proxy URL"),
        help_text="Enforce proxy that alters system "
                  "HTTP_PROXY and HTTPS_PROXY",
        widget=forms.URLInput(),
        required=False)

    max_priority = forms.BooleanField(
        label=_("Max Priority"),
        help_text="Set the cpu process to the "
                  "highest priority (i.e. -20 "
                  "on Linux) and real-time for "
                  "I/O. The process priority "
                  "will be set only if nice and "
                  "ionice are installed Default "
                  "disabled. Use with caution.",
        widget=forms.CheckboxInput(),
        required=False)

    class Meta(object):
        name = _("Advanced Configuration")


class AdvancedConfiguration(workflows.Step):
    action_class = AdvancedConfigurationAction
    contributes = ('exclude',
                   'log_file',
                   'proxy',
                   'max_priority')


class ConfigureBackups(workflows.Workflow):
    slug = "configuration"
    name = _("Configuration")
    finalize_button_name = _("Save")
    success_message = _('Configuration file saved correctly.')
    failure_message = _('Unable to save configuration file.')
    success_url = "horizon:freezer_ui:configurations:index"

    default_steps = (BackupConfiguration,
                     OptionsConfiguration,
                     ClientsConfiguration,
                     SchedulingConfiguration,
                     AdvancedConfiguration)

    @sensitive_variables('encryption_password',
                         'confirm_encryption_password')
    def handle(self, request, context):
        try:
            if context['original_name'] == '':
                freezer_api.configuration_create(
                    request,
                    name=context['name'],
                    container_name=context['container_name'],
                    src_file=context['src_file'],
                    levels=context['levels'],  # if empty save 0 not null
                    optimize=context['optimize'],
                    compression=context['compression'],
                    encryption_password=context['encryption_password'],
                    clients=context['clients'],  # save the name of the client
                    start_datetime=context['start_datetime'],
                    interval=context['interval'],
                    exclude=context['exclude'],
                    log_file=context['log_file'],
                    proxy=context['proxy'],
                    max_priority=context['max_priority'],
                )
            else:
                freezer_api.configuration_update(
                    request,
                    config_id=context['original_name'],
                    name=context['name'],
                    container_name=context['container_name'],
                    src_file=context['src_file'],
                    levels=context['levels'],  # if empty save 0 not null
                    optimize=context['optimize'],
                    compression=context['compression'],
                    encryption_password=context['encryption_password'],
                    clients=context['clients'],  # save the name of the client
                    start_datetime=context['start_datetime'],
                    interval=context['interval'],
                    exclude=context['exclude'],
                    log_file=context['log_file'],
                    proxy=context['proxy'],
                    max_priority=context['max_priority'],
                )
            return True
        except Exception:
            exceptions.handle(request)
            return False
