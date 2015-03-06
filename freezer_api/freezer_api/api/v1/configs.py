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


class ConfigsCollectionResource(object):
    """
    Handler for endpoint: /v1/configs
    """

    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp):
        user_id = req.get_header('X-User-ID') or ''
        offset = req.get_param('offset') or ''
        limit = req.get_param_as_int('limit') or 10
        search = req.context.get('doc', {})
        obj_list = self.db.get_config(user_id=user_id, offset=offset,
                                      limit=limit, search=search)
        req.context['result'] = {'configs': obj_list}

    def on_post(self, req, resp):
        try:
            doc = req.context['doc']
        except KeyError:
            raise exceptions.BadDataFormat(
                message='Missing request body',
                resp_body={'error': 'missing request body'})

        user_name = req.get_header('X-User-Name')
        user_id = req.get_header('X-User-ID')
        config_id = self.db.add_config(
            user_id=user_id, user_name=user_name, doc=doc)
        resp.status = falcon.HTTP_201
        req.context['result'] = {'config_id': config_id}


class ConfigsResource(object):
    """
    Handler for endpoint: /v1/configs/{config_id}
    """
    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp, config_id):
        user_id = req.get_header('X-User-ID')
        obj = self.db.get_config(user_id=user_id, config_id=config_id)
        req.context['result'] = obj

    def on_delete(self, req, resp, config_id):
        user_id = req.get_header('X-User-ID')
        self.db.delete_config(
            user_id=user_id, config_id=config_id)
        req.context['result'] = {'config_id': config_id}
        resp.status = falcon.HTTP_204

    def on_patch(self, req, resp, config_id):
        # PATCH /v1/configs/{config_id}
        user_id = req.get_header('X-User-ID') or ''
        patch = req.context.get('doc', {})
        new_version = self.db.update_config(user_id=user_id,
                                            config_id=config_id,
                                            patch=patch)
        req.context['result'] = {'config_id': config_id,
                                 'patch': patch,
                                 'version': new_version}
