from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.devfreezer import dashboard


class Freezerweb(horizon.Panel):
    name = _("Freezer")
    slug = "freezerweb"


dashboard.Devfreezer.register(Freezerweb)
