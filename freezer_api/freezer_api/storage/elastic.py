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
from freezer_api.common.utils import JobDoc
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
        match_not_list = [{"match": m} for m in search.get('match_not', [])]
        base_filter.append({"query": {"bool": {"must": match_list, "must_not": match_not_list}}})
        return base_filter

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        try:
            base_filter = TypeManager.get_base_search_filter(user_id, search)
            query_filter = {"filter": {"bool": {"must": base_filter}}}
            return {'query': {'filtered': query_filter}}
        except:
            raise exceptions.StorageEngineError(
                message='search operation failed: query not valid')

    def get(self, user_id, doc_id):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.doc_type,
                              id=doc_id)
            doc = res['_source']
        except elasticsearch.TransportError:
            raise exceptions.DocumentNotFound(
                message='No document found with ID {0}'.format(doc_id))
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='Get operation failed: {0}'.format(e))
        if doc['user_id'] != user_id:
            raise exceptions.AccessForbidden("Document access forbidden")
        return doc

    def search(self, user_id, doc_id=None, search={}, offset=0, limit=10):
        query_dsl = self.get_search_query(user_id, doc_id, search)
        try:
            res = self.es.search(index=self.index, doc_type=self.doc_type,
                                 size=limit, from_=offset, body=query_dsl)
        except elasticsearch.ConnectionError:
            raise exceptions.StorageEngineError(
                message='unable to connecto to db server')
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
            version = res['_version']
        except Exception as e:
            raise exceptions.StorageEngineError(
                message='index operation failed {0}'.format(e))
        return (created, version)

    def delete(self, user_id, doc_id):
        query_dsl = self.get_search_query(user_id, doc_id)
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


class JobTypeManager(TypeManager):
    def __init__(self, es, doc_type, index='freezer'):
        TypeManager.__init__(self, es, doc_type, index=index)

    @staticmethod
    def get_search_query(user_id, doc_id, search={}):
        base_filter = TypeManager.get_base_search_filter(user_id, search)
        if doc_id is not None:
            base_filter.append({"term": {"job_id": doc_id}})
        query_filter = {"filter": {"bool": {"must": base_filter}}}
        return {'query': {'filtered': query_filter}}

    def update(self, job_id, job_update_doc):
        update_doc = {"doc": job_update_doc}
        try:
            res = self.es.update(index=self.index, doc_type=self.doc_type,
                                 id=job_id, body=update_doc)
            version = res['_version']
        except elasticsearch.TransportError:
            raise exceptions.DocumentNotFound(
                message='Unable to find job to update '
                        'with id {0} '.format(job_id))
        except Exception:
            raise exceptions.StorageEngineError(
                message='Unable to update job with id {0}'.format(job_id))
        return version


class ElasticSearchEngine(object):

    def __init__(self, hosts, index='freezer'):
        self.index = index
        self.es = elasticsearch.Elasticsearch(hosts)
        logging.info('Using Elasticsearch host {0}'.format(hosts))
        self.backup_manager = BackupTypeManager(self.es, 'backups')
        self.client_manager = ClientTypeManager(self.es, 'clients')
        self.job_manager = JobTypeManager(self.es, 'jobs')

    def get_backup(self, user_id, backup_id=None,
                   offset=0, limit=10, search={}):
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
        self.backup_manager.insert(backup_metadata_doc.serialize())
        return backup_id

    def delete_backup(self, user_id, backup_id):
        return self.backup_manager.delete(user_id, backup_id)

    def get_client(self, user_id, client_id=None,
                   offset=0, limit=10, search={}):
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
                message=('Client already registered with '
                         'ID {0}'.format(client_id)))
        client_doc = {'client': doc,
                      'user_id': user_id}
        self.client_manager.insert(client_doc)
        logging.info('Client registered, client_id: {0}'.
                     format(client_id))
        return client_id

    def delete_client(self, user_id, client_id):
        return self.client_manager.delete(user_id, client_id)

    def get_job(self, user_id, job_id):
        return self.job_manager.get(user_id, job_id)

    def search_job(self, user_id, offset=0, limit=10, search={}):
        return self.job_manager.search(user_id,
                                       search=search,
                                       offset=offset,
                                       limit=limit)

    def add_job(self, user_id, doc):
        jobdoc = JobDoc.create(doc, user_id)
        job_id = jobdoc['job_id']
        self.job_manager.insert(jobdoc, job_id)
        logging.info('Job registered, job id: {0}'.
                     format(job_id))
        return job_id

    def delete_job(self, user_id, job_id):
        return self.job_manager.delete(user_id, job_id)

    def update_job(self, user_id, job_id, patch_doc):
        valid_patch = JobDoc.create_patch(patch_doc)

        # check that document exists
        assert (self.job_manager.get(user_id, job_id))

        version = self.job_manager.update(job_id, valid_patch)
        logging.info('Job {0} updated to version {1}'.
                     format(job_id, version))
        return version

    def replace_job(self, user_id, job_id, doc):
        # check that no document exists with
        # same job_id and different user_id
        try:
            self.job_manager.get(user_id, job_id)
        except exceptions.DocumentNotFound:
            pass

        valid_doc = JobDoc.update(doc, user_id, job_id)

        (created, version) = self.job_manager.insert(valid_doc, job_id)
        if created:
            logging.info('Job {0} created'.format(job_id, version))
        else:
            logging.info('Job {0} replaced with version {1}'.
                         format(job_id, version))
        return version
