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


class TypeManager:
    def __init__(self, es, doc_type, index):
        self.es = es
        self.index = index
        self.doc_type = doc_type

    @staticmethod
    def get_base_search_filter(user_id, search={}):
        user_id_filter = {"term": {"user_id": user_id}}
        base_filter = [user_id_filter]
        match_list = [{"match": m} for m in search.get('match', [])]
        if match_list:
            base_filter.append({"query": {"bool": {"must": match_list}}})
        return base_filter

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        return {"filter": {"bool": {"must": base_filter}}}

    def search(self, user_id, doc_id, search={}, offset=0, limit=10):
        try:
            query_dsl = self.get_search_query(user_id, doc_id, search)
        except:
            raise exceptions.StorageEngineError(
                message='search operation failed: query not valid',
                resp_body={'engine exception': 'invalid query'})
        try:
            res = self.es.search(index=self.index, doc_type=self.doc_type,
                                 size=limit, from_=offset, body=query_dsl)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='search operation failed',
                resp_body={'engine exception': '{0}'.format(e)})
        hit_list = res['hits']['hits']
        return [x['_source'] for x in hit_list]

    def insert(self, doc):
        try:
            res = self.es.index(index=self.index, doc_type=self.doc_type,
                                body=doc)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='index operation failed',
                resp_body={'engine exception': '{0}'.format(e)})
        return res['created']

    def delete(self, user_id, doc_id):
        try:
            query_dsl = self.get_search_query(user_id, doc_id)
        except:
            raise exceptions.StorageEngineError(
                message='delete operation failed: query not valid',
                resp_body={'engine exception': 'invalid query'})
        try:
            self.es.delete_by_query(index=self.index,
                                    doc_type=self.doc_type,
                                    body=query_dsl)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='delete operation failed',
                resp_body={'engine exception': '{0}'.format(e)})
        return doc_id


class BackupTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"backup_id": doc_id}})

        if 'time_after' in search:
            base_filter.append(
                {"range": {"timestamp": {"gte": int(search['time_after'])}}}
            )

        if 'time_before' in search:
            base_filter.append(
                {"range": {"timestamp": {"lte": int(search['time_before'])}}}
            )
        return {"filter": {"bool": {"must": base_filter}}}


class ClientTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"client_id": doc_id}})
        return {"filter": {"bool": {"must": base_filter}}}


class ElasticSearchEngine(object):

    def __init__(self, hosts, index='freezer'):
        self.index = index
        self.es = elasticsearch.Elasticsearch(hosts)
        logging.info('Using Elasticsearch host {0}'.format(hosts))
        self.backup_manager = BackupTypeManager(self.es, 'backups')
        self.client_manager = ClientTypeManager(self.es, 'clients')

    def get_backup(self, user_id, backup_id=None, offset=0, limit=10, search={}):
        return self.backup_manager.search(user_id,
                                          backup_id,
                                          search=search,
                                          offset=offset,
                                          limit=limit)

    def add_backup(self, user_id, user_name, doc):
        # raises if data is malformed (HTTP_400) or already present (HTTP_409)
        backup_metadata_doc = BackupMetadataDoc(user_id, user_name, doc)
        if not backup_metadata_doc.is_valid():
            raise exceptions.BadDataFormat(message='Bad Data Format')
        backup_id = backup_metadata_doc.backup_id
        existing = self.backup_manager.search(user_id, backup_id)
        if existing:    # len(existing) > 0
            raise exceptions.DocumentExists(
                message='Backup data already existing ({0})'.format(backup_id),
                resp_body={'backup_id': backup_id})
        if not self.backup_manager.insert(backup_metadata_doc.serialize()):
            raise exceptions.StorageEngineError(
                message='index operation failed',
                resp_body={'backup_id': backup_id})
        logging.info('Backup metadata indexed, backup_id: {0}'.
                     format(backup_id))
        return backup_id

    def delete_backup(self, user_id, backup_id):
        return self.backup_manager.delete(user_id, backup_id)

    def get_client(self, user_id, client_id=None, offset=0, limit=10, search={}):
        return self.client_manager.search(user_id,
                                          client_id,
                                          search=search,
                                          offset=offset,
                                          limit=limit)

    def add_client(self, user_id, doc):
        client_id = doc.get('client_id', None)
        if client_id is None:
            raise exceptions.BadDataFormat(message='Bad Data Format')
        existing = self.client_manager.search(user_id, client_id)
        if existing:    # len(existing) > 0
            raise exceptions.DocumentExists(
                message='Client already registered ({0})'.format(client_id),
                resp_body={'client_id': client_id})
        client_doc = {'client': doc,
                      'user_id': user_id}
        if not self.client_manager.insert(client_doc):
            raise exceptions.StorageEngineError(
                message='index operation failed',
                resp_body={'client_id': client_id})
        logging.info('Client registered, client_id: {0}'.
                     format(client_id))
        return client_id

    def delete_client(self, user_id, client_id):
        return self.client_manager.delete(user_id, client_id)



