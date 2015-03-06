import functools

from django.views import generic

from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.api.rest.utils import JSONResponse

import horizon_web_ui.freezer_ui.api.api as freezer_api


# https://github.com/tornadoweb/tornado/issues/1009
# http://haacked.com/archive/2008/11/20/anatomy-of-a-subtle-json-vulnerability.aspx/
def prevent_json_hijacking(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        response = function(*args, **kwargs)
        if isinstance(response, JSONResponse) and response.content:
            response.content = ")]}',\n" + response.content
        return response

    return wrapper


class Clients(generic.View):
    """API for nova limits."""

    @prevent_json_hijacking
    @rest_utils.ajax()
    def get(self, request):
        """Get all registered freezer clients"""

        # we don't have a "get all clients" api (probably for good reason) so
        # we need to resort to getting a very high number.
        clients = freezer_api.client_list(request, limit=9999)
        clients = [c.get_dict() for c in clients]

        return clients
