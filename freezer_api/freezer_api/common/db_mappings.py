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


clients_mapping = {
    u'properties': {
        u'client': {
            u'properties': {
                u'client_id': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'config_id': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'description': {
                    u'type': u'string',
                },
                u'hostname': {
                    u'type': u'string',
                },
            },
        },
        u'user_id': {
            u'index': u'not_analyzed',
            u'type': u'string',
        },
    },
}

backups_mapping = {
    u'properties': {
        u'backup_id': {
            u'type': u'string',
        },
        u'backup_metadata': {
            u'properties': {
                u'backup_name': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'backup_session': {
                    u'type': u'long',
                },
                u'backup_size_compressed': {
                    u'type': u'long',
                },
                u'backup_size_uncompressed': {
                    u'type': u'long',
                },
                u'broken_links': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'cli': {
                    u'type': u'string',
                },
                u'client_os': {
                    u'type': u'string',
                },
                u'compression_alg': {
                    u'type': u'string',
                },
                u'container': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'encrypted': {
                    u'type': u'boolean',
                },
                u'excluded_files': {
                    u'type': u'string',
                },
                u'fs_real_path': {
                    u'type': u'string',
                },
                u'host_name': {
                    u'index': u'not_analyzed',
                    u'type': u'string',
                },
                u'level': {
                    u'type': u'long',
                },
                u'max_level': {
                    u'type': u'long',
                },
                u'mode': {
                    u'type': u'string',
                },
                u'timestamp': {
                    u'type': u'long',
                },
                u'total_backup_session_size': {
                    u'type': u'long',
                },
                u'total_broken_links': {
                    u'type': u'long',
                },
                u'total_directories': {
                    u'type': u'long',
                },
                u'total_fs_files': {
                    u'type': u'long',
                },
                u'version': {
                    u'type': u'string',
                },
                u'vol_snap_path': {
                    u'type': u'string',
                },
            },
        },
        u'user_id': {
            u'index': u'not_analyzed',
            u'type': u'string',
        },
        u'user_name': {
            u'type': u'string',
        },
    },
}

jobs_mapping = {
    "properties": {
        "client_id": {
            "index": "not_analyzed",
            "type": "string"
        },
        "description": {
            "type": "string"
        },
        "job_actions": {
            "properties": {
                "freezer_action": {
                    "properties": {
                        "action": {
                            "type": "string"
                        },
                        "backup_name": {
                            "type": "string"
                        },
                        "container": {
                            "type": "string"
                        },
                        "dry_run": {
                            "type": "boolean"
                        },
                        "lvm_auto_snap": {
                            "type": "string"
                        },
                        "lvm_dirmount": {
                            "type": "string"
                        },
                        "lvm_snapname": {
                            "type": "string"
                        },
                        "lvm_snapsize": {
                            "type": "string"
                        },
                        "max_level": {
                            "type": "long"
                        },
                        "max_priority": {
                            "type": "boolean"
                        },
                        "max_segment_size": {
                            "type": "long"
                        },
                        "mode": {
                            "type": "string"
                        },
                        "mysql_conf": {
                            "type": "string"
                        },
                        "path_to_backup": {
                            "type": "string"
                        },
                        "remove_older_than": {
                            "type": "long"
                        },
                        "remove_older_then": {
                            "type": "long"
                        },
                        "restore_abs_path": {
                            "type": "string"
                        }
                    }
                },
                "mandatory": {
                    "type": "boolean"
                },
                "max_retries": {
                    "type": "long"
                },
                "max_retries_interval": {
                    "type": "long"
                }
            }
        },
        "job_event": {
            "type": "string"
        },
        "job_id": {
            "index": "not_analyzed",
            "type": "string"
        },
        "job_schedule": {
            "properties": {
                "event": {
                    "type": "string"
                },
                "result": {
                    "type": "string"
                },
                "schedule_day_of_week": {
                    "type": "string"
                },
                "schedule_hour": {
                    "type": "string"
                },
                "schedule_interval": {
                    "type": "string"
                },
                "schedule_minute": {
                    "type": "string"
                },
                "schedule_start_date": {
                    "format": "dateOptionalTime",
                    "type": "date"
                },
                "status": {
                    "type": "string"
                },
                "time_created": {
                    "type": "long"
                },
                "time_ended": {
                    "type": "long"
                },
                "time_started": {
                    "type": "long"
                }
            }
        },
        "session_id": {
            "type": "string",
            "index": "not_analyzed"
        },
        "session_tag": {
            "type": "long"
        },
        "user_id": {
            "index": "not_analyzed",
            "type": "string"
        }
    }
}


def get_mappings():
    return {
        u'jobs': jobs_mapping,
        u'backups': backups_mapping,
        u'clients': clients_mapping
    }
