from horizon import views

from horizon import tabs

from openstack_dashboard.dashboards.devfreezer.freezerweb \
    import tabs as mydashboard_tabs 

class IndexView(tabs.TabbedTableView):
    tab_group_class = mydashboard_tabs.MypanelTabs
    # A very simple class-based view...
    template_name = 'devfreezer/freezerweb/index.html'

    def get_data(self, request, context, *args, **kwargs):
        # Add data to the context here...
        return context

