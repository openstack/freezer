from horizon import browsers
from horizon import tabs
from horizon import exceptions

from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property  # noqa
from openstack_dashboard import api
from openstack_dashboard.dashboards.freezer.freezerpanel \
    import tabs as freezer_tabs
from openstack_dashboard.dashboards.freezer.freezerpanel \
    import browsers as freezer_browsers

class IndexView(tabs.TabbedTableView):
    tab_group_class = freezer_tabs.MypanelTabs
    template_name = 'freezer/freezerpanel/index.html'

    def get_data(self, request, context, *args, **kwargs):
        # Add data to the context here...
        return context

class BackupView(browsers.ResourceBrowserView):
    browser_class = freezer_browsers.ContainerBrowser
    template_name = "freezer/freezerpanel/container.html"

    def get_containers_data(self):
        containers = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        try:
            containers, self._more = api.swift.swift_get_containers(
                self.request, marker=marker)
        except Exception:
            msg = _('Unable to retrieve container list.')
            exceptions.handle(self.request, msg)
        return containers

    @cached_property
    def objects(self):
        """Returns a list of objects given the subfolder's path.

        The path is from the kwargs of the request.
        """
        objects = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        container_name = self.kwargs['container_name']
        subfolder = self.kwargs['subfolder_path']
        prefix = None
        if container_name:
            self.navigation_selection = True
            if subfolder:
                prefix = subfolder
            try:
                objects, self._more = api.swift.swift_get_objects(
                    self.request,
                    container_name,
                    marker=marker,
                    prefix=prefix)
            except Exception:
                self._more = None
                objects = []
                msg = _('Unable to retrieve object list.')
                exceptions.handle(self.request, msg)
        return objects

    def is_subdir(self, item):
        content_type = "application/pseudo-folder"
        return getattr(item, "content_type", None) == content_type

    def is_placeholder(self, item):
        object_name = getattr(item, "name", "")
        return object_name.endswith(api.swift.FOLDER_DELIMITER)

    def get_objects_data(self):
        """Returns a list of objects within the current folder."""
        filtered_objects = [item for item in self.objects
                            if (not self.is_subdir(item) and
                                not self.is_placeholder(item))]
        return filtered_objects

    def get_subfolders_data(self):
        """Returns a list of subfolders within the current folder."""
        filtered_objects = [item for item in self.objects
                            if self.is_subdir(item)]
        return filtered_objects

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['subfolders'] = []
        if self.kwargs["subfolder_path"]:
            (parent, slash, folder) = self.kwargs["subfolder_path"] \
                                          .strip('/').rpartition('/')
            while folder:
                path = "%s%s%s/" % (parent, slash, folder)
                context['subfolders'].insert(0, (folder, path))
                (parent, slash, folder) = parent.rpartition('/')
        return context
