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
from horizon_web_ui.freezer_ui.utils import timestamp_to_string


def format_last_backup(last_backup):
    last_backup_ts = datetime.datetime.fromtimestamp(last_backup)
    ten_days_later = last_backup_ts + datetime.timedelta(days=10)
    today = datetime.datetime.today()

    if last_backup is None:
        colour = 'red'
        icon = 'fire'
        text = 'Never'
    elif ten_days_later < today:
        colour = 'orange'
        icon = 'thumbs-down'
        text = timestamp_to_string(last_backup)
    else:
        colour = 'green'
        icon = 'thumbs-up'
        text = timestamp_to_string(last_backup)

    return safestring.mark_safe(
        '<span style="color:{}"><span class="glyphicon glyphicon-{}" aria-hidd'
        'en="true"></span> {}</span>'.format(colour, icon, text))


class AttachJobToSession(tables.LinkAction):
    name = "attach_job_to_session"
    verbose_name = _("Attach To Session")
    classes = ("ajax-modal")
    url = "horizon:freezer_ui:sessions:attach"

    def allowed(self, request, instance):
        return True

    def get_link_url(self, datum):
        return reverse("horizon:freezer_ui:sessions:attach",
                       kwargs={'job_id': datum.job_id})


class Restore(tables.Action):
    name = "restore"
    verbose_name = _("Restore")

    def single(self, table, request, instance):
        messages.info(request, "Needs to be implemented")

    def allowed(self, request, instance):
        return True


class DeleteJob(tables.DeleteAction):
    name = "delete"
    classes = ("btn-danger",)
    icon = "remove"
    help_text = _("Delete jobs is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Job File",
            u"Delete Job Files",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Job File",
            u"Deleted Job Files",
            count
        )

    def delete(self, request, obj_id):
        return freezer_api.job_delete(request, obj_id)


class DeleteMultipleJobs(DeleteJob):
    name = "delete_multiple_jobs"


class CloneJob(tables.Action):
    name = "clone"
    verbose_name = _("Clone Job")
    help_text = _("Clone and edit a job file")

    def single(self, table, request, obj_id):
        freezer_api.job_clone(request, obj_id)
        return shortcuts.redirect('horizon:freezer_ui:jobs:index')


class EditJob(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Job")
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, datum=None):
        return reverse("horizon:freezer_ui:jobs:configure",
                       kwargs={'backup_name': datum.job_id})


def get_backup_configs_link(backup_config):
    return reverse('horizon:freezer_ui:jobs:index',
                   kwargs={'job_id': backup_config.job_id})


class CreateJob(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Job")
    url = "horizon:freezer_ui:jobs:create"
    classes = ("ajax-modal",)
    icon = "plus"


class CreateAction(tables.LinkAction):
    name = "create_action"
    verbose_name = _("Create Action")
    url = "horizon:freezer_ui:jobs:create_action"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        return reverse("horizon:freezer_ui:jobs:create_action",
                       kwargs={'job_id': datum.job_id})


class JobsTable(tables.DataTable):
    job_name = tables.Column("description",
                             link=get_backup_configs_link,
                             verbose_name=_("Job Name"))

    result = tables.Column("result",
                           verbose_name=_("Job Result"))

    def get_object_id(self, backup_config):
        return backup_config.id

    class Meta(object):
        name = "jobs"
        verbose_name = _("Jobs")
        table_actions = (CreateJob,
                         DeleteMultipleJobs)
        footer = False
        multi_select = True
        row_actions = (CreateAction,
                       EditJob,
                       AttachJobToSession,
                       CloneJob,
                       DeleteJob,)


class DeleteAction(tables.DeleteAction):
    name = "delete"
    classes = ("btn-danger",)
    icon = "remove"
    help_text = _("Delete actions is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Action",
            u"Delete Action",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted action File",
            u"Deleted action Files",
            count
        )

    def delete(self, request, obj_id):
        freezer_api.action_delete(request, obj_id)
        return reverse("horizon:freezer_ui:jobs:index")


class DeleteMultipleActions(DeleteAction):
    name = "delete_multiple_actions"


class EditAction(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, datum=None):
        # this is used to pass to values as an url
        # TODO: look for a way to improve this
        ids = '{0}==={1}'.format(datum.action_id, datum.job_id)
        return reverse("horizon:freezer_ui:jobs:create_action",
                       kwargs={'job_id': ids})


class ObjectFilterAction(tables.FilterAction):
    def allowed(self, request, datum):
        return bool(self.table.kwargs['job_id'])


class ActionsTable(tables.DataTable):
    action_name = tables.Column('action',
                                verbose_name=_("Action Type"))

    backup_name = tables.Column('backup_name',
                                verbose_name=_("Action Name"))

    def get_object_id(self, container):
        # this is used to pass to values as an url
        # TODO: look for a way to improve this
        ids = '{0}==={1}'.format(container.action_id, container.job_id)
        return ids

    class Meta(object):
        name = "status"
        verbose_name = _("Status")
        table_actions = (ObjectFilterAction,
                         DeleteMultipleActions)
        row_actions = (EditAction,
                       DeleteAction,)
        footer = False
        multi_select = True
