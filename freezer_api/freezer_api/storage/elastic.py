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

import elasticsearch
import logging
from freezer_api.common.utils import BackupMetadataDoc
from freezer_api.common.utils import ConfigDoc
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
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}

    def get(self, user_id, doc_id):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.doc_type,
                              id=doc_id)
            doc = res['_source']
            if doc['user_id'] != user_id:
                raise elasticsearch.TransportError()
        except elasticsearch.TransportError:
            raise exceptions.DocumentNotFound(
                message='No document found with ID {0}'.format(doc_id))
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='Get operation failed: {0}'.format(e))
        return doc

    def search(self, user_id, doc_id=None, search={}, offset=0, limit=10):
        try:
            query_dsl = self.get_search_query(user_id, doc_id, search)
        except:
            raise exceptions.StorageEngineError(
                message='search operation failed: query not valid')
        try:
            res = self.es.search(index=self.index, doc_type=self.doc_type,
                                 size=limit, from_=offset, body=query_dsl)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='search operation failed: {0}'.format(e))
        hit_list = res['hits']['hits']
        return [x['_source'] for x in hit_list]

    def insert(self, doc, doc_id=None):
        try:
            res = self.es.index(index=self.index, doc_type=self.doc_type,
                                body=doc, id=doc_id)
            created = res['created']
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='index operation failed {0}'.format(e))
        return created

    def delete(self, user_id, doc_id):
        try:
            query_dsl = self.get_search_query(user_id, doc_id)
        except:
            raise exceptions.StorageEngineError(
                message='Delete operation failed: query not valid')
        try:
            self.es.delete_by_query(index=self.index,
                                    doc_type=self.doc_type,
                                    body=query_dsl)
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='Delete operation failed: {0}'.format(e))
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
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}


class ClientTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"client_id": doc_id}})
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}


class ActionTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"action_id": doc_id}})
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}

    def update(self, action_id, action_update_doc):
        update_doc = {"doc": action_update_doc}
        try:
            res = self.es.update(index=self.index, doc_type=self.doc_type,
                                 id=action_id, body=update_doc)
            version = res['_version']
        except elasticsearch.TransportError:
            raise exceptions.DocumentNotFound(
                message='Unable to find action to update '
                        'with ID {0} '.format(action_id))
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='Unable to update action, '
                        'action ID: {0} '.format(action_id))
        return version


class ConfigTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"config_id": doc_id}})
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}

    def update(self, config_id, config_update_doc):
        update_doc = {'doc': config_update_doc}
        try:
            print config_update_doc
            res = self.es.update(index=self.index,
                                 doc_type=self.doc_type,
                                 id=config_id,
                                 body=update_doc)
            print 'here?'
            version = res['_version']
        except elasticsearch.TransportError as error:
            raise exceptions.DocumentNotFound(
                message='Unable to find configuration file to update '
                        'with ID {0}'.format(config_id))
        except Exception as error:
            raise exceptions.StorageEngineError(
                message='Unable to update configuration file, '
                        'config ID {0}'.format(config_id))
        return version


class ElasticSearchEngine(object):

    def __init__(self, hosts, index='freezer'):
        self.index = index
        self.es = elasticsearch.Elasticsearch(hosts)
        logging.info('Using Elasticsearch host {0}'.format(hosts))
        self.backup_manager = BackupTypeManager(self.es, 'backups')
        self.client_manager = ClientTypeManager(self.es, 'clients')
        self.action_manager = ActionTypeManager(self.es, 'actions')
        self.config_manager = ConfigTypeManager(self.es, 'configs')

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
                message='Backup data already existing '
                        'with ID {0}'.format(backup_id))
        if not self.backup_manager.insert(backup_metadata_doc.serialize()):
            raise exceptions.StorageEngineError(
                message='Index operation failed, '
                        'backup ID: {0}'.format(backup_id))
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
            raise exceptions.BadDataFormat(message='Missing client ID')
        existing = self.client_manager.search(user_id, client_id)
        if existing:    # len(existing) > 0
            raise exceptions.DocumentExists(
                message='Client already registered with ID {0}'.format(client_id))
        client_doc = {'client': doc,
                      'user_id': user_id}
        if not self.client_manager.insert(client_doc):
            raise exceptions.StorageEngineError(
                message='Index operation failed, '
                        'client ID: {0}'.format(client_id))
        logging.info('Client registered, client_id: {0}'.
                     format(client_id))
        return client_id

    def delete_client(self, user_id, client_id):
        return self.client_manager.delete(user_id, client_id)

    def get_action(self, user_id, action_id):
        return self.action_manager.get(user_id, action_id)

    def search_action(self, user_id, offset=0, limit=10, search={}):
        return self.action_manager.search(user_id,
                                          search=search,
                                          offset=offset,
                                          limit=limit)

    def add_action(self, user_id, doc):
        action_id = doc.get('action_id', None)
        if action_id is None:
            raise exceptions.BadDataFormat(message='Missing action ID')
        action_doc = {'action': doc,
                      'user_id': user_id}
        if not self.action_manager.insert(action_doc, action_id):
            raise exceptions.StorageEngineError(
                message='Index operation failed, '
                        ' action ID: {0}'.format(action_id))
        logging.info('Action registered, action ID: {0}'.
                     format(action_id))
        return action_id

    def delete_action(self, user_id, action_id):
        return self.action_manager.delete(user_id, action_id)

    def update_action(self, user_id, action_id, patch):
        if 'action_id' in patch:
            raise exceptions.BadDataFormat(
                message='Action ID modification is not allowed, '
                        'action ID: {0}'.format(action_id))
        action_doc = self.action_manager.get(user_id, action_id)
        action_doc['action'].update(patch)
        version = self.action_manager.update(action_id, action_doc)
        logging.info('Action {0} updated to version {1}'.
                     format(action_id, version))
        return version

    def add_config(self, user_id, user_name, doc):
        config_doc = ConfigDoc(user_id, user_name, doc)
        config_doc = config_doc.serialize()
        config_id = config_doc['config_id']

        if config_id is None:
            raise exceptions.BadDataFormat(message='Missing config ID')

        if not self.config_manager.insert(config_doc,
                                          doc_id=config_id):
            raise exceptions.StorageEngineError(
                message='Index operation failed, '
                        ' config ID: {0}'.format(config_id))
        logging.info('Config registered, config ID: {0}'.
                     format(config_id))
        return config_id

    def delete_config(self, user_id, config_id):
        return self.config_manager.delete(user_id, config_id)

    def get_config(self, user_id, config_id=None,
                   offset=0, limit=10, search={}):
        return self.config_manager.search(user_id,
                                          config_id,
                                          search=search,
                                          offset=offset,
                                          limit=limit)

    def update_config(self, user_id, config_id, patch,
                      offset=0, limit=10, search={}):

        if 'config_id' in patch:
            raise exceptions.BadDataFormat(
                message='Config ID modification is not allowed, '
                        ' config ID: {0}'.format(config_id))
        config_doc = self.config_manager.search(user_id,
                                                config_id,
                                                search=search,
                                                offset=offset,
                                                limit=limit)[0]
        config_doc['config_file'].update(patch)
        version = self.config_manager.update(config_id, config_doc)
        logging.info('Configuration file {0} updated to version {1}'.
                     format(config_id, version))
        return version
