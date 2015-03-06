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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import workflows

from horizon import browsers
from horizon import exceptions
import horizon_web_ui.freezer_ui.api.api as freezer_api
import horizon_web_ui.freezer_ui.configurations.browsers as project_browsers
import workflows.configure as configure_workflow


LOG = logging.getLogger(__name__)


class ConfigureWorkflowView(workflows.WorkflowView):
    workflow_class = configure_workflow.ConfigureBackups

    def get_object(self, *args, **kwargs):
        config_id = self.kwargs['name']
        try:
            return freezer_api.configuration_get(self.request, config_id)[0]
        except Exception:
            redirect = reverse("horizon:freezer_ui:configurations:index")
            msg = _('Unable to retrieve details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def is_update(self):
        return 'name' in self.kwargs and bool(self.kwargs['name'])

    def get_initial(self):
        initial = super(ConfigureWorkflowView, self).get_initial()
        if self.is_update():
            initial.update({'original_name': None})
            config = self.get_object()
            initial['name'] = config.name
            initial['container_name'] = config.container_name
            initial['config_id'] = config.config_id
            initial['src_file'] = config.src_file
            initial['levels'] = config.levels
            initial['optimize'] = config.optimize
            initial['compression'] = config.compression
            initial['encryption_password'] = config.encryption_password
            initial['start_datetime'] = config.start_datetime
            initial['interval'] = config.interval
            initial['exclude'] = config.exclude
            initial['log_file'] = config.log_file
            initial['encryption_password'] = config.encryption_password
            initial['proxy'] = config.proxy
            initial['max_priority'] = config.max_priority
            initial['clients'] = config.clients
            initial['original_name'] = config.config_id
            initial.update({'original_name': config.config_id})
        return initial


class BackupConfigsView(browsers.ResourceBrowserView):
    browser_class = project_browsers.ContainerBrowser
    template_name = "freezer_ui/configurations/browser.html"

    def get_backup_configuration_data(self):
        configurations = []
        try:
            configurations = freezer_api.configuration_list(self.request)
        except Exception:
            msg = _('Unable to retrieve configuration file list.')
            exceptions.handle(self.request, msg)
        return configurations

    def get_clients_data(self):
        configuration = []
        try:
            if self.kwargs['config_id']:
                configuration = freezer_api.clients_in_config(
                    self.request, self.kwargs['config_id'])

        except Exception:
            msg = _('Unable to retrieve instances for this configuration.')
            exceptions.handle(self.request, msg)
        return configuration
