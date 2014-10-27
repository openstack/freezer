from django.utils.translation import ugettext_lazy as _

import horizon


class Devfreezer(horizon.Dashboard):
    name = _("Backup as a Service")
    slug = "devfreezer"
    panels = ('freezerweb',)  # Add your panels here.
    default_panel = 'freezerweb'  # Specify the slug of the dashboard's default panel.


horizon.register(Devfreezer)
