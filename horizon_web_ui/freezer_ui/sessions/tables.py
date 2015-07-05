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
from django import shortcuts
from django.utils import safestring
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import messages
from horizon import tables
from horizon.utils.urlresolvers import reverse

import horizon_web_ui.freezer_ui.api.api as freezer_api
from horizon_web_ui.freezer_ui.django_utils import timestamp_to_string


def get_link(session):
    return reverse('horizon:freezer_ui:sessions:index',
                   kwargs={'session_id': session.session_id})


class CreateJob(tables.LinkAction):
    name = "create_session"
    verbose_name = _("Create Session")
    url = "horizon:freezer_ui:sessions:create"
    classes = ("ajax-modal",)
    icon = "plus"


class DeleteSession(tables.DeleteAction):
    name = "delete"
    classes = ("btn-danger",)
    icon = "remove"
    help_text = _("Delete sessions is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Session",
            u"Delete Sessions",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Session",
            u"Deleted Sessions",
            count
        )

    def delete(self, request, session_id):
        return freezer_api.session_delete(request, session_id)


class EditSession(tables.LinkAction):
    name = "edit_session"
    verbose_name = _("Edit Session")
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, datum=None):
        return reverse("horizon:freezer_ui:sessions:edit",
                       kwargs={'session_id': datum.session_id})


class DeleteMultipleActions(DeleteSession):
    name = "delete_multiple_actions"


class DeleteJobFromSession(tables.DeleteAction):
    name = "delete_job_from_session"
    classes = ("btn-danger",)
    icon = "remove"
    help_text = _("Delete jobs is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Job",
            u"Delete Jobs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Job",
            u"Deleted Jobs",
            count
        )

    def delete(self, request, session):
        job_id, session_id = session.split('===')
        return freezer_api.remove_job_from_session(
            request,
            session_id,
            job_id)


class JobsTable(tables.DataTable):
    client_id = tables.Column(
        'client_id',
        verbose_name=_("Client ID"))

    status = tables.Column(
        'status',
        verbose_name=_("Status"))

    def get_object_id(self, job):
        # this is used to pass to values as an url
        # TODO: look for a way to improve this
        ids = '{0}==={1}'.format(job.job_id, job.session_id)
        return ids

    class Meta(object):
        name = "jobs"
        verbose_name = _("Jobs")
        table_actions = ()
        row_actions = (DeleteJobFromSession,)
        footer = False
        multi_select = True


class SessionsTable(tables.DataTable):
    description = tables.Column('description',
                                link=get_link,
                                verbose_name=_("Session"))

    status = tables.Column('status',
                           verbose_name=_("Status"))

    def get_object_id(self, session):
        return session.session_id

    class Meta(object):
        name = "sessions"
        verbose_name = _("Sessions")
        table_actions = (CreateJob,
                         DeleteMultipleActions)
        row_actions = (EditSession,
                       DeleteSession,)
        footer = False
        multi_select = True
