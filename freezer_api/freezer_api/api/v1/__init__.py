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

from freezer_api.api.v1 import backups
from freezer_api.api.v1 import clients
from freezer_api.api.v1 import homedoc

VERSION = {
    'id': '1',
    'status': 'CURRENT',
    'updated': '2015-03-23T13:45:00',
    'links': [
        {
            'href': '/v1/',
            'rel': 'self'
        }
    ]
}


def public_endpoints(storage_driver):
    return [
        ('/',
         homedoc.Resource()),

        ('/backups',
         backups.BackupsCollectionResource(storage_driver)),

        ('/backups/{backup_id}',
         backups.BackupsResource(storage_driver)),

        ('/clients',
         clients.ClientsCollectionResource(storage_driver)),

        ('/clients/{client_id}',
         clients.ClientsResource(storage_driver)),

    ]
