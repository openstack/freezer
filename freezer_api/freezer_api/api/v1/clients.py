"""
Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================
"""

import falcon
from freezer_api.common import exceptions


class ClientsCollectionResource(object):
    """
    Handler for endpoint: /v1/clients
    """
    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp):
        # GET /v1/clients(?limit,offset)     Lists backups
        user_id = req.get_header('X-User-ID')
        offset = req.get_param_as_int('offset') or 0
        limit = req.get_param_as_int('limit') or 10
        search = req.context.get('doc', {})
        obj_list = self.db.get_client(user_id=user_id, offset=offset,
                                      limit=limit, search=search)
        req.context['result'] = {'clients': obj_list}

    def on_post(self, req, resp):
        # POST /v1/clients    Creates client entry
        try:
            doc = req.context['doc']
        except KeyError:
            raise exceptions.BadDataFormat(
                message='Missing request body')
        user_id = req.get_header('X-User-ID')
        client_id = self.db.add_client(
            user_id=user_id, doc=doc)
        resp.status = falcon.HTTP_201
        req.context['result'] = {'client_id': client_id}


class ClientsResource(object):
    """
    Handler for endpoint: /v1/clients/{client_id}
    """
    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp, client_id):
        # GET /v1/clients(?limit,offset)
        # search in body
        user_id = req.get_header('X-User-ID') or ''
        obj = self.db.get_client(user_id=user_id, client_id=client_id)
        if obj:
            req.context['result'] = obj[0]
        else:
            resp.status = falcon.HTTP_404

    def on_delete(self, req, resp, client_id):
        # DELETE /v1/clients/{client_id}     Deletes the specified backup
        user_id = req.get_header('X-User-ID')
        self.db.delete_client(
            user_id=user_id, client_id=client_id)
        req.context['result'] = {'client_id': client_id}
        resp.status = falcon.HTTP_204
