from django.utils.translation import ugettext_lazy as _

import horizon


class Mygroup(horizon.PanelGroup):
    slug = "mygroup"
    name = _("Freezer")
    panels = ('freezerpanel',)


class Freezer(horizon.Dashboard):
    name = _("Backup-aaS")
    slug = "freezer"
    panels = (Mygroup,)  # Add your panels here.
    default_panel = 'freezerpanel'  # Specify the slug of the default panel.


horizon.register(Freezer)