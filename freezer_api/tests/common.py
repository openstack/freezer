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


import io


fake_data_0_backup_id = 'freezer_container_alpha_important_data_backup_8475903425_0'
fake_data_0_user_id = 'qwerty1234'
fake_data_0_user_name = 'asdffdsa'

fake_data_0_wrapped_backup_metadata = {
    'backup_id': 'freezer_container_alpha_important_data_backup_8475903425_0',
    'user_id': 'qwerty1234',
    'user_name': 'asdffdsa',
    'backup_metadata': {
        "container": "freezer_container",
        "host_name": "alpha",
        "backup_name": "important_data_backup",
        "timestamp": 8475903425,
        "level": 0,
        "backup_session": 8475903425,
        "max_level": 5,
        "mode" : "fs",
        "fs_real_path": "/blabla",
        "vol_snap_path": "/blablasnap",
        "total_broken_links" : 0,
        "total_fs_files" : 11,
        "total_directories" : 2,
        "backup_size_uncompressed" : 4567,
        "backup_size_compressed" : 1212,
        "total_backup_session_size" : 6789,
        "compression_alg": "None",
        "encrypted": "false",
        "client_os": "linux",
        "broken_links": ["link_01", "link_02"],
        "excluded_files": ["excluded_file_01", "excluded_file_02"],
        "cli": ""
    }
}

fake_data_0_backup_metadata = {
    "container": "freezer_container",
    "host_name": "alpha",
    "backup_name": "important_data_backup",
    "timestamp": 8475903425,
    "level": 0,
    "backup_session": 8475903425,
    "max_level": 5,
    "mode": "fs",
    "fs_real_path": "/blabla",
    "vol_snap_path": "/blablasnap",
    "total_broken_links" : 0,
    "total_fs_files" : 11,
    "total_directories" : 2,
    "backup_size_uncompressed" : 4567,
    "backup_size_compressed" : 1212,
    "total_backup_session_size" : 6789,
    "compression_alg": "None",
    "encrypted": "false",
    "client_os": "linux",
    "broken_links": ["link_01", "link_02"],
    "excluded_files": ["excluded_file_01", "excluded_file_02"],
    "cli": ""
}

fake_malformed_data_0_backup_metadata = {
    "host_name": "alpha",
    "backup_name": "important_data_backup",
    "timestamp": 8475903425,
    "level": 0,
    "backup_session": 8475903425,
    "max_level": 5,
    "mode": "fs",
    "fs_real_path": "/blabla",
    "vol_snap_path": "/blablasnap",
    "total_broken_links" : 0,
    "total_fs_files" : 11,
    "total_directories" : 2,
    "backup_size_uncompressed" : 4567,
    "backup_size_compressed" : 1212,
    "total_backup_session_size" : 6789,
    "compression_alg": "None",
    "encrypted": "false",
    "client_os": "linux",
    "broken_links": ["link_01", "link_02"],
    "excluded_files": ["excluded_file_01", "excluded_file_02"],
    "cli": ""
}


fake_data_0_elasticsearch_hit = {
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [
            {
                "_id": "AUx_iu-ewlhuOVELWtH0",
                "_index": "freezer",
                "_score": 1.0,
                "_type": "backups",
                "_source": {
                    "container": "freezer_container",
                    "host_name": "alpha",
                    "backup_name": "important_data_backup",
                    "timestamp": 8475903425,
                    "level": 0,
                    "backup_session": 8475903425,
                    "max_level": 5,
                    "mode" : "fs",
                    "fs_real_path": "/blabla",
                    "vol_snap_path": "/blablasnap",
                    "total_broken_links" : 0,
                    "total_fs_files" : 11,
                    "total_directories" : 2,
                    "backup_size_uncompressed" : 4567,
                    "backup_size_compressed" : 1212,
                    "total_backup_session_size" : 6789,
                    "compression_alg": "None",
                    "encrypted": "false",
                    "client_os": "linux",
                    "broken_links": ["link_01", "link_02"],
                    "excluded_files": ["excluded_file_01", "excluded_file_02"],
                    "cli": ""
                }
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": False,
    "took": 3
}


fake_data_0_elasticsearch_miss = {
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [],
        "max_score": None,
        "total": 0
    },
    "timed_out": False,
    "took": 1
}


class FakeReqResp:

    def __init__(self, method='GET', body=''):
        self.method = method
        self.body = body
        self.stream = io.BytesIO(body)
        self.content_length = len(body)
        self.context = {}
        self.header = {}

    def get_header(self, key):
        return self.header.get(key, None)


class FakeElasticsearch_hit:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        return fake_data_0_elasticsearch_hit

    def index(self, index, doc_type, body):
        return {'created': True}

    def delete_by_query(self, index, doc_type, q):
        pass


class FakeElasticsearch_insert_ok:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        return fake_data_0_elasticsearch_miss

    def index(self, index, doc_type, body):
        return {'created': True}

    def delete_by_query(self, index, doc_type, q):
        pass


class FakeElasticsearch_miss:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        return fake_data_0_elasticsearch_miss

    def index(self, index, doc_type, body):
        return {'created': False}

    def delete_by_query(self, index, doc_type, q):
        pass


class FakeElasticsearch_index_raise:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        return fake_data_0_elasticsearch_miss

    def index(self, index, doc_type, body):
        raise Exception

    def delete_by_query(self, index, doc_type, q):
        pass


class FakeElasticsearch_search_raise:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        raise Exception

    def index(self, index, doc_type, body):
        return {'created': True}

    def delete_by_query(self, index, doc_type, q):
        pass

class FakeElasticsearch_delete_raise:
    def __init__(self, host=None):
        pass

    def search(self, index, doc_type, q):
        return fake_data_0_elasticsearch_miss

    def index(self, index, doc_type, body):
        return {'created': True}

    def delete_by_query(self, index, doc_type, q):
        raise Exception


class FakeLogging:

    def __init__(self):
        return None

    def __call__(self, *args, **kwargs):
        return True

    @classmethod
    def logging(cls, opt1=True):
        return True

    @classmethod
    def info(cls, opt1=True):
        return True

    @classmethod
    def warning(cls, opt1=True):
        return True

    @classmethod
    def critical(cls, opt1=True):
        return True

    @classmethod
    def exception(cls, opt1=True):
        return True

    @classmethod
    def error(cls, opt1=True):
        return True
