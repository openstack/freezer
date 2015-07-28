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

import datetime
import pprint

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import date as django_date
from django.views import generic

from horizon import exceptions
from horizon import tables
from horizon import workflows


from horizon_web_ui.freezer_ui.backups import tables as freezer_tables
from horizon_web_ui.freezer_ui.backups.workflows import restore as restore_workflow
import horizon_web_ui.freezer_ui.api.api as freezer_api


class IndexView(tables.DataTableView):
    name = _("Backups")
    slug = "backups"
    table_class = freezer_tables.BackupsTable
    template_name = "freezer_ui/backups/index.html"

    def get_data(self):
        backups, self._has_more = freezer_api.backups_list(self.request)
        return backups


class DetailView(generic.TemplateView):
    template_name = 'freezer_ui/backups/detail.html'

    def get_context_data(self, **kwargs):

        backup = freezer_api.backup_get(self.request, kwargs['backup_id'])
        return {'data': pprint.pformat(backup.data_dict)}


class RestoreView(workflows.WorkflowView):
    workflow_class = restore_workflow.Restore

    def get_object(self, *args, **kwargs):
        id = self.kwargs['backup_id']
        try:
            return freezer_api.backup_get(self.request, id)
        except Exception:
            redirect = reverse("horizon:freezer_ui:backups:index")
            msg = _('Unable to retrieve details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def is_update(self):
        return 'name' in self.kwargs and bool(self.kwargs['name'])

    def get_workflow_name(self):
        backup = freezer_api.backup_get(self.request, self.kwargs['backup_id'])
        backup_date = datetime.datetime.fromtimestamp(
            int(backup.data_dict[0]['backup_metadata']['time_stamp']))
        backup_date_str = django_date(backup_date, 'SHORT_DATETIME_FORMAT')
        return "Restore '{}' from {}".format(
            backup.data_dict[0]['backup_metadata']['backup_name'], backup_date_str)

    def get_initial(self):
        return {"backup_id": self.kwargs['backup_id']}

    def get_workflow(self, *args, **kwargs):
        workflow = super(RestoreView, self).get_workflow(*args, **kwargs)
        workflow.name = self.get_workflow_name()

        return workflow

