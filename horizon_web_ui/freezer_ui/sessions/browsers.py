# Copyright 2012 Nebula, Inc.
# Copyright 2015 Hewlett-Packard
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.translation import ugettext_lazy as _
from horizon import browsers
from horizon_web_ui.freezer_ui.sessions import tables


class SessionBrowser(browsers.ResourceBrowser):
    name = "session_configuration"
    verbose_name = _("Session Configuration")
    navigation_table_class = tables.SessionsTable
    content_table_class = tables.JobsTable
    navigable_item_name = _("Sessions")
    navigation_kwarg_name = "session_id"
