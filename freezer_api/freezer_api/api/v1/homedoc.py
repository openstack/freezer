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

http://tools.ietf.org/html/draft-nottingham-json-home-03
"""

import json

HOME_DOC = {
    'resources': {
        'rel/backups': {
            'href-template': '/v1/backups/{backup_id}',
            'href-vars': {
                'backup_id': 'param/backup_id'
            },
            'hints': {
                'allow': ['GET'],
                'formats': {
                    'application/json': {},
                },
            },
        },
    }
}


class Resource(object):

    def __init__(self):
        document = json.dumps(HOME_DOC, ensure_ascii=False, indent=4)
        self.document_utf8 = document.encode('utf-8')

    def on_get(self, req, resp):
        resp.data = self.document_utf8
        resp.content_type = 'application/json-home'
