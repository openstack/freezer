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


class Restore(tables.Action):
    name = "restore"
    verbose_name = _("Restore")

    def single(self, table, request, instance):
        messages.info(request, "Needs to be implemented")

    def allowed(self, request, instance):
        return True


class DeleteConfig(tables.DeleteAction):
    name = "delete"
    classes = ("btn-danger",)
    icon = "remove"
    help_text = _("Delete configurations are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Configuration File",
            u"Delete Configuration Files",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Configuration File",
            u"Deleted Configuration Files",
            count
        )

    def delete(self, request, obj_id):
        return freezer_api.configuration_delete(request, obj_id)


class CloneConfig(tables.Action):
    name = "clone"
    verbose_name = _("Clone")
    # classes = ("ajax-modal",)
    help_text = _("Clone and edit a configuration file")

    def single(self, table, request, obj_id):
        freezer_api.configuration_clone(request, obj_id)
        return shortcuts.redirect('horizon:freezer_ui:configurations:index')


class EditConfig(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    classes = ("ajax-modal",)

    def get_link_url(self, datum=None):
        return reverse("horizon:freezer_ui:configurations:configure",
                       kwargs={'name': datum.config_id})


def get_backup_configs_link(backup_config):
    return reverse('horizon:freezer_ui:configurations:index',
                   kwargs={'config_id': backup_config.config_id})


class CreateConfig(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Configuration")
    url = "horizon:freezer_ui:configurations:create"
    classes = ("ajax-modal",)
    icon = "plus"


class BackupConfigsTable(tables.DataTable):
    name = tables.Column("name", link=get_backup_configs_link,
                         verbose_name=_("Configuration Name"))

    def get_object_id(self, backup_config):
        return backup_config.id

    class Meta(object):
        name = "backup_configuration"
        verbose_name = _("Backup Configurations")
        table_actions = (CreateConfig,)
        footer = False
        multi_select = False
        row_actions = (EditConfig,
                       CloneConfig,
                       DeleteConfig, )


class ObjectFilterAction(tables.FilterAction):
    def allowed(self, request, datum):
        return bool(self.table.kwargs['config_id'])


class InstancesTable(tables.DataTable):
    client = tables.Column('name', verbose_name=_("Client Name"))

    created = tables.Column('last_backup',
                            filters=(format_last_backup,),
                            verbose_name=_("Last backup"))

    def get_object_id(self, container):
        return container.name

    class Meta(object):
        name = "clients"
        verbose_name = _("Clients")
        table_actions = (ObjectFilterAction,)
        row_actions = (Restore,)
        footer = False
        multi_select = False
