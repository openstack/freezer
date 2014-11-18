from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.freezer.freezerpanel import tables


class ContainerTab(tabs.TableTab):
    name = _("Backups Tab")
    slug = "instances_tab"
    table_classes = (tables.ContainersTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._has_more

    def get_containers_data(self):
        try:
            marker = self.request.GET.get(
                        tables.ContainersTable._meta.pagination_param, None)
            containers, self._has_more = api.swift.swift_get_containers(self.request, marker)
            print '{}'.format(containers)
            return containers
        except Exception:
            self._has_more = False
            error_message = _('Unable to get instances')
            exceptions.handle(self.request, error_message)

            return []

class MypanelTabs(tabs.TabGroup):
    slug = "mypanel_tabs"
    tabs = (ContainerTab,)
    sticky = True