"""
Copyright 2015 Hewlett-Packard

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


class JobsCollectionResource(object):
    """
    Handler for endpoint: /v1/jobs
    """
    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp):
        # GET /v1/jobs(?limit,offset)     Lists jobs
        user_id = req.get_header('X-User-ID')
        offset = req.get_param_as_int('offset') or 0
        limit = req.get_param_as_int('limit') or 10
        search = req.context.get('doc', {})
        obj_list = self.db.search_job(user_id=user_id, offset=offset,
                                      limit=limit, search=search)
        req.context['result'] = {'jobs': obj_list}

    def on_post(self, req, resp):
        # POST /v1/jobs    Creates job entry
        try:
            doc = req.context['doc']
        except KeyError:
            raise freezer_api_exc.BadDataFormat(
                message='Missing request body')

        user_id = req.get_header('X-User-ID')
        job_id = self.db.add_job(user_id=user_id, doc=doc)
        resp.status = falcon.HTTP_201
        req.context['result'] = {'job_id': job_id}


class JobsResource(object):
    """
    Handler for endpoint: /v1/jobs/{job_id}
    """

    def __init__(self, storage_driver):
        self.db = storage_driver

    def on_get(self, req, resp, job_id):
        # GET /v1/jobs/{job_id}     retrieves the specified job
        # search in body
        user_id = req.get_header('X-User-ID') or ''
        obj = self.db.get_job(user_id=user_id, job_id=job_id)
        if obj:
            req.context['result'] = obj
        else:
            resp.status = falcon.HTTP_404

    def on_delete(self, req, resp, job_id):
        # DELETE /v1/jobs/{job_id}     Deletes the specified job
        user_id = req.get_header('X-User-ID')
        self.db.delete_job(user_id=user_id, job_id=job_id)
        req.context['result'] = {'job_id': job_id}
        resp.status = falcon.HTTP_204

    def on_patch(self, req, resp, job_id):
        # PATCH /v1/jobs/{job_id}     updates the specified job
        user_id = req.get_header('X-User-ID') or ''
        doc = req.context.get('doc', {})
        new_version = self.db.update_job(user_id=user_id,
                                         job_id=job_id,
                                         patch_doc=doc)
        req.context['result'] = {'job_id': job_id,
                                 'version': new_version}

    def on_post(self, req, resp, job_id):
        # PUT /v1/jobs/{job_id}     creates/replaces the specified job
        user_id = req.get_header('X-User-ID') or ''
        doc = req.context.get('doc', {})
        new_version = self.db.replace_job(user_id=user_id,
                                          job_id=job_id,
                                          doc=doc)
        resp.status = falcon.HTTP_201
        req.context['result'] = {'job_id': job_id,
                                 'version': new_version}
