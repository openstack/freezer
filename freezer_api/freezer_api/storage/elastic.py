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

import elasticsearch
import logging
from freezer_api.common.utils import BackupMetadataDoc
from freezer_api.common import exceptions


class ElasticSearchEngine(object):

    def __init__(self, hosts):
        # logging.getLogger('elasticsearch').addHandler(logging.NullHandler())
        self.es = elasticsearch.Elasticsearch(hosts)
        logging.info('Using Elasticsearch host {0}'.format(hosts))
        self.index = "freezer"

    def _get_backup(self, user_id, backup_id=None):
        # raises only on severe engine errors
        if backup_id:
            query = '+user_id:{0} +backup_id:{1}'.format(user_id, backup_id)
        else:
            query = '+user_id:{0}'.format(user_id)
        try:
            res = self.es.search(index=self.index, doc_type='backups',
                                 q=query)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='search operation failed',
                resp_body={'engine exception': '{0}'.format(e)})
        hit_list = res['hits']['hits']
        return [x['_source'] for x in hit_list]

    def _index(self, doc):
        # raises only on severe engine errors
        try:
            res = self.es.index(index=self.index, doc_type='backups',
                                body=doc)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='index operation failed',
                resp_body={'engine exception': '{0}'.format(e)})
        return res['created']

    def _delete_backup(self, user_id, backup_id):
        query = '+user_id:{0} +backup_id:{1}'.format(user_id, backup_id)
        try:
            self.es.delete_by_query(index=self.index,
                                    doc_type='backups',
                                    q=query)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='search operation failed',
                resp_body={'engine exception': '{0}'.format(e)})

    def get_backup(self, user_id, backup_id):
        # raises is data not found, so reply will be HTTP_404
        backup_metadata = self._get_backup(user_id, backup_id)
        if not backup_metadata:
            raise exceptions.ObjectNotFound(
                message='Requested backup data not found: {0}'.
                format(backup_id),
                resp_body={'backup_id': backup_id})
        return backup_metadata

    def get_backup_list(self, user_id):
        # TODO: elasticsearch reindex for paging
        return self._get_backup(user_id)

    def add_backup(self, user_id, user_name, data):
        # raises if data is malformed (HTTP_400) or already present (HTTP_409)
        backup_metadata_doc = BackupMetadataDoc(user_id, user_name, data)
        if not backup_metadata_doc.is_valid():
            raise exceptions.BadDataFormat(message='Bad Data Format')
        backup_id = backup_metadata_doc.backup_id
        existing_data = self._get_backup(user_id, backup_id)
        if existing_data:
            raise exceptions.DocumentExists(
                message='Backup data already existing ({0})'.format(backup_id),
                resp_body={'backup_id': backup_id})
        if not self._index(backup_metadata_doc.serialize()):
            # should never happen
            raise exceptions.StorageEngineError(
                message='index operation failed',
                resp_body={'backup_id': backup_id})
        logging.info('Backup metadata indexed, backup_id: {0}'.
                     format(backup_id))
        return backup_id

    def delete_backup(self, user_id, backup_id):
        self._delete_backup(user_id, backup_id)
        return backup_id
