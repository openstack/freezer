# Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
import datetime
import pprint
import time

from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as django_date
from django.utils.translation import ugettext_lazy as _
from django.views import generic
import parsedatetime as pdt

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon import workflows
from horizon_web_ui.freezer_ui.backups import tables as freezer_tables

import horizon_web_ui.freezer_ui.api.api as freezer_api
import restore_workflow


class IndexView(tables.DataTableView):
    name = _("Backups")
    slug = "backups"
    table_class = freezer_tables.BackupsTable
    template_name = ("freezer_ui/backups/index.html")

    def has_more_data(self, table):
        return self._has_more

    def get_data(self):
        filter = self.get_filters(self.request,
                                  self.table.get_filter_field(),
                                  self.table.get_filter_string())

        backups, self._has_more = freezer_api.backups_list(
            self.request,
            offset=self.table.offset,
            time_after=filter['from'],
            time_before=filter['to'],
            text_match=filter['contains']
        )

        return backups

    def get_filters(self, request, filter_field, filter_string):
        cal = pdt.Calendar()

        filters = {}
        filters['from'] = None
        filters['to'] = None
        filters['contains'] = None

        if filter_field == 'between':
            result_range = cal.nlp(filter_string)

            if result_range and len(result_range) == 2:
                filters['from'] = int(
                    time.mktime(result_range[0][0].timetuple()))
                filters['to'] = int(
                    time.mktime(result_range[1][0].timetuple()))
            else:
                messages.warning(
                    request,
                    "Please enter two dates. E.g: '01/01/2014 - 05/09/2015'.")
        elif filter_field in ['before', 'after']:
            result, what = cal.parse(filter_string)

            if what == 0:
                messages.warning(
                    self.table.request,
                    "Please enter a date/time. E.g: '01/01/2014 12pm' or '1 we"
                    "ek ago'.")
            else:
                field = 'to' if filter_field == 'before' else 'from'

                dt = datetime.datetime(*result[:6])

                if what == 1:  # a date without time
                    # use .date() to remove time part
                    filters[field] = int(time.mktime(dt.date().timetuple()))
                elif what in [2, 3]:  # date and time or time with current date
                    filters[field] = int(time.mktime(dt.timetuple()))
                else:
                    raise Exception(
                        'Unknown result when parsing date: {}'.format(what))
        elif filter_field == 'contains':
            filters['contains'] = filter_string.lower()

        return filters


class DetailView(generic.TemplateView):
    template_name = 'freezer_ui/backups/detail.html'

    def get_context_data(self, **kwargs):

        backup = freezer_api.get_backup(self.request, kwargs['backup_id'])
        return {'data': pprint.pformat(backup.data_dict)}


class RestoreView(workflows.WorkflowView):
    workflow_class = restore_workflow.ConfigureBackups

    def get_object(self, *args, **kwargs):
        id = self.kwargs['backup_id']
        try:
            return freezer_api.get_backup(self.request, id)
        except Exception:
            redirect = reverse("horizon:freezer_ui:backups:index")
            msg = _('Unable to retrieve details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def is_update(self):
        return 'name' in self.kwargs and bool(self.kwargs['name'])

    def get_workflow_name(self):
        backup = freezer_api.backup_get(self.request, self.kwargs['backup_id'])
        backup_date = datetime.datetime.fromtimestamp(int(backup.timestamp))
        backup_date_str = django_date(backup_date, 'SHORT_DATETIME_FORMAT')
        return "Restore '{}' from {}".format(
            backup.backup_name, backup_date_str)

    def get_initial(self):
        return {"backup_id": self.kwargs['backup_id']}

    def get_workflow(self, *args, **kwargs):
        workflow = super(RestoreView, self).get_workflow(*args, **kwargs)
        workflow.name = self.get_workflow_name()

        return workflow
