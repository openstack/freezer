#  Licensed under the Apache License, Version 2.0 (the "License"); you may
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

from django.utils.translation import ugettext_lazy as _

import horizon


class Mygroup(horizon.PanelGroup):
    slug = "mygroup"
    name = _("Freezer")
    panels = ('overview', 'configurations', 'backups', 'actions')


class Freezer(horizon.Dashboard):
    name = _("Backup Restore DR")
    slug = "freezer_ui"
    panels = (Mygroup,)
    default_panel = 'overview'


horizon.register(Freezer)
