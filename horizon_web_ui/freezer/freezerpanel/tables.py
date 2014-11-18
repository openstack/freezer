from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from horizon.utils.urlresolvers import reverse  # noqa
from openstack_dashboard import api
from django.template import defaultfilters as filters
from django.utils import http
from django.utils import safestring

from django import template

from horizon import tables

LOADING_IMAGE = safestring.mark_safe('<img src="/static/dashboard/img/loading.gif" />')

def get_metadata(container):
    # If the metadata has not been loading, display a loading image
    if not get_metadata_loaded(container):
        return LOADING_IMAGE
    template_name = 'freezer/freezerpanel/_container_metadata.html'
    context = {"container": container}
    return template.loader.render_to_string(template_name, context)

def wrap_delimiter(name):
    if name and not name.endswith(api.swift.FOLDER_DELIMITER):
        return name + api.swift.FOLDER_DELIMITER
    return name

def get_container_link(container):
    return reverse("horizon:freezer:freezerpanel:index",
                   args=(wrap_delimiter(container.name),))

def get_metadata_loaded(container):
    # Determine if metadata has been loaded if the attribute is already set.
    return hasattr(container, 'is_public') and container.is_public is not None

class ContainerAjaxUpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, container_name):
        container = api.swift.swift_get_container(request,
                                                  container_name,
                                                  with_data=False)
        return container


class ContainersTable(tables.DataTable):
    METADATA_LOADED_CHOICES = (
        (False, None),
        (True, True),
    )
    name = tables.Column("name", link=get_container_link,
                         verbose_name=_("Name"))
    bytes = tables.Column(lambda x: x.container_bytes_used if get_metadata_loaded(x) else LOADING_IMAGE
                          , verbose_name=_("Size"))
    count = tables.Column(lambda x: x.container_object_count if get_metadata_loaded(x) else LOADING_IMAGE
                          , verbose_name=_("Object count"))
    metadata = tables.Column(get_metadata,
                             verbose_name=_("Container Details"),
                             classes=('nowrap-col', ),)

    metadata_loaded = tables.Column(get_metadata_loaded,
                                    status=True,
                                    status_choices=METADATA_LOADED_CHOICES,
                                    hidden=True)
    def get_object_id(self, container):
        return container.name

    def get_absolute_url(self):
        url = super(ContainersTable, self).get_absolute_url()
        return http.urlquote(url)

    def get_full_url(self):
        """Returns the encoded absolute URL path with its query string."""
        url = super(ContainersTable, self).get_full_url()
        return http.urlquote(url)

    class Meta:
        name = "containers"
        verbose_name = _("Backups")
        row_class = ContainerAjaxUpdateRow
        status_columns = ['metadata_loaded', ]


class ObjectFilterAction(tables.FilterAction):
    def _filtered_data(self, table, filter_string):
        request = table.request
        container = self.table.kwargs['container_name']
        subfolder = self.table.kwargs['subfolder_path']
        prefix = wrap_delimiter(subfolder) if subfolder else ''
        self.filtered_data = api.swift.swift_filter_objects(request,
                                                            filter_string,
                                                            container,
                                                            prefix=prefix)
        return self.filtered_data

    def filter_subfolders_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type == "application/pseudo-folder"]

    def filter_objects_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type != "application/pseudo-folder"]

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False

def get_link_subfolder(subfolder):
    container_name = subfolder.container_name
    return reverse("horizon:freezer:freezerpanel:index",
                   args=(wrap_delimiter(container_name),
                         wrap_delimiter(subfolder.name)))

def sanitize_name(name):
    return name.split(api.swift.FOLDER_DELIMITER)[-1]


def get_size(obj):
    if obj.bytes is None:
        return _("pseudo-folder")
    return filters.filesizeformat(obj.bytes)

class DeleteObject(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Object",
            u"Delete Objects",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Object",
            u"Deleted Objects",
            count
        )

    name = "delete_object"
    allowed_data_types = ("objects", "subfolders",)

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        container_name = obj.container_name
        datum_type = getattr(obj, self.table._meta.data_type_name, None)
        if datum_type == 'subfolders':
            obj_id = obj_id[(len(container_name) + 1):] + "/"
        api.swift.swift_delete_object(request, container_name, obj_id)

    def get_success_url(self, request):
        url = super(DeleteObject, self).get_success_url(request)
        return http.urlquote(url)


class DeleteMultipleObjects(DeleteObject):
    name = "delete_multiple_objects"

class CreatePseudoFolder(tables.FilterAction):
    def _filtered_data(self, table, filter_string):
        request = table.request
        container = self.table.kwargs['container_name']
        subfolder = self.table.kwargs['subfolder_path']
        prefix = wrap_delimiter(subfolder) if subfolder else ''
        self.filtered_data = api.swift.swift_filter_objects(request,
                                                            filter_string,
                                                            container,
                                                            prefix=prefix)
        return self.filtered_data

    def filter_subfolders_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type == "application/pseudo-folder"]

    def filter_objects_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type != "application/pseudo-folder"]

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False

class ObjectsTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_link_subfolder,
                         allowed_data_types=("subfolders",),
                         verbose_name=_("Object Name"),
                         filters=(sanitize_name,))

    size = tables.Column(get_size, verbose_name=_('Size'))

    class Meta:
        name = "objects"
        verbose_name = _("Objects")
        table_actions = (ObjectFilterAction,
                         DeleteMultipleObjects)
        data_types = ("subfolders", "objects")
        browser_table = "content"
        footer = False

    def get_absolute_url(self):
        url = super(ObjectsTable, self).get_absolute_url()
        return http.urlquote(url)

    def get_full_url(self):
        """Returns the encoded absolute URL path with its query string.

        This is used for the POST action attribute on the form element
        wrapping the table. We use this method to persist the
        pagination marker.

        """
        url = super(ObjectsTable, self).get_full_url()
        return http.urlquote(url)