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

import logging

from oslo_config import cfg

from freezer_api.storage import elastic


opt_group = cfg.OptGroup(name='storage',
                         title='Freezer Storage Engine')

storage_opts = [
    cfg.StrOpt('db',
               default='elasticsearch',
               help='specify the storage db to use: elasticsearch (default)'),
    cfg.StrOpt('endpoint',
               default='http://localhost:9200',
               help='specify the storage endpoint')
]

CONF = cfg.CONF
CONF.register_group(opt_group)
CONF.register_opts(storage_opts, opt_group)


def get_db():
    db_engine = CONF.storage.db
    if db_engine == 'elasticsearch':
        endpoint = CONF.storage.endpoint
        logging.info('Storage backend: Elasticsearch at {0}'.format(endpoint))
        db = elastic.ElasticSearchEngine(endpoint)
    else:
        raise Exception('Database Engine {0} not supported'.format(db_engine))
    return db
