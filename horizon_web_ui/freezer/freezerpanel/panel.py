from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.freezer import dashboard


class Freezerpanel(horizon.Panel):
    name = _("Admin")
    slug = "freezerpanel"


dashboard.Freezer.register(Freezerpanel)
