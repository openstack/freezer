"""Freezer swift.py related tests

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


import unittest

import pytest

from freezer_api.storage import elastic

from common import *
from freezer_api.common.exceptions import *

import elasticsearch


class TestElasticSearchEngine:

    def patch_logging(self, monkeypatch):
        fakelogging = FakeLogging()
        monkeypatch.setattr(logging, 'critical', fakelogging.critical)
        monkeypatch.setattr(logging, 'warning', fakelogging.warning)
        monkeypatch.setattr(logging, 'exception', fakelogging.exception)
        monkeypatch.setattr(logging, 'error', fakelogging.error)


class TestElasticSearchEngine_get_backup(TestElasticSearchEngine):

    def test_get_backup_userid_and_backup_id_return_ok(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_hit)
        engine = elastic.ElasticSearchEngine('host')
        res = engine.get_backup(fake_data_0_user_id, fake_data_0_backup_id)
        assert (res == [fake_data_0_backup_metadata, ])

    def test_get_backup_raises_when_query_has_no_hits(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_miss)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(ObjectNotFound, engine.get_backup, fake_data_0_user_id, fake_data_0_backup_id)


class TestElasticSearchEngine_get_backup_list(TestElasticSearchEngine):

    def test_get_backup_list_return_ok(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_hit)
        engine = elastic.ElasticSearchEngine('host')
        res = engine.get_backup_list(fake_data_0_user_id)
        assert (res == [fake_data_0_backup_metadata, ])


class TestElasticSearchEngine_add_backup(TestElasticSearchEngine):

    def test_index_backup_success(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_insert_ok)
        engine = elastic.ElasticSearchEngine('host')
        res = engine.add_backup(fake_data_0_user_id, fake_data_0_user_name, fake_data_0_backup_metadata)
        assert (res == fake_data_0_backup_id)

    def test_index_backup_raise_when_data_exists(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_hit)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(DocumentExists, engine.add_backup, fake_data_0_user_id,
                      fake_data_0_user_name, fake_data_0_backup_metadata)

    def test_index_backup_raise_when_es_index_raises(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_index_raise)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(StorageEngineError, engine.add_backup, fake_data_0_user_id,
                      fake_data_0_user_name, fake_data_0_backup_metadata)

    def test_index_backup_raise_when_es_search_raises(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_search_raise)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(StorageEngineError, engine.add_backup, fake_data_0_user_id,
                      fake_data_0_user_name, fake_data_0_backup_metadata)

    def test_index_backup_raise_when_data_is_malformed(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_insert_ok)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(BadDataFormat, engine.add_backup, fake_data_0_user_id,
                      fake_data_0_user_name, fake_malformed_data_0_backup_metadata)


class TestElasticSearchEngine_delete_backup(TestElasticSearchEngine):

    def test_delete_backup_raise_when_es_delete_raises(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_delete_raise)
        engine = elastic.ElasticSearchEngine('host')
        pytest.raises(StorageEngineError, engine.delete_backup, fake_data_0_user_id, fake_data_0_backup_id)

    def test_delete_backup_ok(self, monkeypatch):
        self.patch_logging(monkeypatch)
        monkeypatch.setattr(elasticsearch, 'Elasticsearch', FakeElasticsearch_hit)
        engine = elastic.ElasticSearchEngine('host')
        res = engine.delete_backup(fake_data_0_user_id, fake_data_0_backup_id)
        assert (res == fake_data_0_backup_id)

