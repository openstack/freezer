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
import copy

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

fake_job_0_user_id = "f4db4da085f043059441565720b217c7"
fake_job_0_job_id = "e7181e5e-2c75-43f8-92c0-c037ae5f11e4"

fake_job_0_elasticsearch_not_found = {
    "_id": "e7181e5e-2c75-43f8-92c0-c037ae5f11e43",
    "_index": "freezer",
    "_type": "job",
    "found": False
}

fake_job_0 = {
  "job_action": {
      "action": "backup",
      "mode": "fs",
      "src_file": "/home/tylerdurden/project_mayhem",
      "backup_name": "project_mayhem_backup",
      "container": "my_backup_container"
  },
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended": 1234,
    "status": "stop",
    "schedule_date": "2015-06-02T16:20:00",
    "schedule_interval": "2 days"
  },
  "job_id": "e7181e5e-2c75-43f8-92c0-c037ae5f11e4",
  "client_id": "mytenantid_myhostname",
  "user_id": "f4db4da085f043059441565720b217c7",
  "description": "test action 4"
}

def get_fake_job_0():
    return copy.deepcopy(fake_job_0)

def get_fake_job_1():
    return copy.deepcopy(fake_job_1)

fake_job_0_elasticsearch_found = {
    "_id": "e7181e5e-2c75-43f8-92c0-c037ae5f11e4",
    "_index": "freezer",
    "_source": fake_job_0,
    "_type": "actions",
    "_version": 1,
    "found": True
}


fake_job_1 = {
  "job_action": {
      "action": "backup",
      "mode": "fs",
      "src_file": "/home/tylerdurden/project_mayhem",
      "backup_name": "project_mayhem_backup",
      "container": "my_backup_container",
  },
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended": 0,
    "status": "invalid",
    "schedule_time": "2015-06-02T16:20:00"
  },
  "job_id": "1b05e367-7832-42df-850e-bc48eabee04e",
  "client_id": "mytenantid_myhostname",
  "user_id": "f4db4da085f043059441565720b217c7",
  "description": "test action 4"
}

# fake_action_1 = {
#             "action_id": "1b05e367-7832-42df-850e-bc48eabee04e",
#             "client_id": "mytenantid_myhostname",
#             "description": "test action 4",
#             "job": {
#                 "action": "restore",
#                 "backup-name": "project_mayhem_backup",
#                 "container": "my_backup_container",
#                 "max_cpu_priority": True,
#                 "restore-abs-path": "/home/tylerdurden/project_mayhem",
#                 "restore-from-host": "another_host"
#             },
#             "status": "pending",
#             "time_created": 1431100962,
#             "time_end": 0,
#             "time_start": 0
# }
#
# fake_action_1_doc = {
#         "action": fake_action_1,
#         "user_id": "f4db4da085f043059441565720b217c7"
#     }
#
#
fake_data_1_wrapped_backup_metadata = {
    'backup_id': 'freezer_container_alpha_important_data_backup_125235431_1',
    'user_id': 'qwerty1234',
    'user_name': 'asdffdsa',
    'backup_metadata': {
        "container": "freezer_container",
        "host_name": "alpha",
        "backup_name": "important_data_backup",
        "timestamp": 125235431,
        "level": 1,
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

fake_client_info_0 = {
  "client_id": "test-tenant_5253_test-hostname_09544",
  "description": "some usefule text here",
  "config_id": "config_id_contains_uuid_of_config"
}

fake_client_info_1 = {
  "client_id": "test-tenant_5253_test-hostname_6543",
  "description": "also some useful text here",
  "config_id": "config_id_blablawhatever"
}

fake_client_entry_0 = {
  "client" : fake_client_info_0,
  "user_id": "user_id-is-provided-keystone"
}

fake_client_entry_1 = {
  "client" : fake_client_info_0,
  "user_id": "user_id-is-provided-keystone"
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
