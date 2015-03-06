# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import functions as utils

from horizon_web_ui.freezer_ui.django_utils import timestamp_to_string


class ActionsTable(tables.DataTable):
    METADATA_LOADED_CHOICES = (
        (False, None),
        (True, True),
    )

    STATUS_DISPLAY = (
        ('pending', 'Pending'),
        ('started', 'Started'),
        ('abort_req', 'Abort Requested'),
        ('aborting', 'Aborting'),
        ('aborted', 'Aborted'),
        ('success', 'Success'),
        ('fail', 'Failed')
    )

    TYPE_DISPLAY = (
        ('restore', 'Restore'),
        ('backup', 'Backup (Unscheduled)')
    )

    client_id = tables.Column("client_id", verbose_name=_("Client Id"))
    type = tables.Column('action', verbose_name=_("Type"),
                         display_choices=TYPE_DISPLAY)
    description = tables.Column("description", verbose_name=_("Description"))
    status = tables.Column('status',
                           verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY)
    created = tables.Column('time_created', verbose_name=_("Created"),
                            filters=(timestamp_to_string,))
    started = tables.Column('time_started', verbose_name=_("Started"),
                            filters=(timestamp_to_string,))
    ended = tables.Column('time_ended', verbose_name=_("Ended"),
                          filters=(timestamp_to_string,))

    def get_object_id(self, action):
        return action.id

    def __init__(self, *args, **kwargs):
        super(ActionsTable, self).__init__(*args,  **kwargs)

        if 'offset' in self.request.GET:
            self.offset = self.request.GET['offset']
        else:
            self.offset = 0

    def get_pagination_string(self):
        page_size = utils.get_page_size(self.request)
        return "=".join(['offset', str(self.offset + page_size)])

    class Meta(object):
        name = "jobs"
        verbose_name = _("Jobs")
