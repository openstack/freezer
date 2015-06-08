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

job_action_properties = {
                "action": {
                    "id": "action",
                    "type": "string"
                },
                "mode": {
                    "id": "mode",
                    "type": "string"
                },
                "src_file": {
                    "id": "src_file",
                    "type": "string"
                },
                "backup_name": {
                    "id": "backup_name",
                    "type": "string"
                },
                "container": {
                    "id": "container",
                    "type": "string"
                }
            }

job_schedule_properties = {
                "time_created": {
                    "id": "time_created",
                    "type": "integer"
                },
                "time_started": {
                    "id": "time_started",
                    "type": "integer"
                },
                "time_ended": {
                    "id": "time_ended",
                    "type": "integer"
                },
                "event": {
                    "id": "event",
                    "type": "string",
                    "enum": ["", "stop", "start", "abort", "remove"]
                },
                "status": {
                    "id": "status",
                    "type": "string",
                    "enum": ["completed", "stop", "scheduled", "running", "aborting", "removed"]
                },
                "result": {
                    "id": "result",
                    "type": "string",
                    "enum": ["", "success", "fail", "aborted"]
                },
                "schedule_date": {
                    "id": "schedule_date",
                    "type": "string",
                    "pattern": "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
                },
                "schedule_interval": {
                    "id": "schedule_interval",
                    "type": "string",
                    "pattern": "^(continuous|(\d+ +(weeks|weeks|days|hours|minutes|seconds)))$"
                },
                "schedule_start_date": {
                    "id": "schedule_start_date",
                    "type": "string",
                    "pattern": "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
                },
                "schedule_end_date": {
                    "id": "schedule_end_date",
                    "type": "string",
                    "pattern": "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
                },
                "schedule_year": {
                    "id": "schedule_year",
                    "type": "string",
                    "pattern": "^\d{4}$"
                },
                "schedule_month": {
                    "id": "schedule_month",
                    "type": "string"
                },
                "schedule_day": {
                    "id": "schedule_day",
                    "type": "string"
                },
                "schedule_week": {
                    "id": "schedule_week",
                    "type": "string"
                },
                "schedule_day_of_week": {
                    "id": "schedule_day_of_week",
                    "type": "string"
                },
                "schedule_hour": {
                    "id": "schedule_hour",
                    "type": "string"
                },
                "schedule_minute": {
                    "id": "schedule_minute",
                    "type": "string"
                },
                "schedule_second": {
                    "id": "schedule_second",
                    "type": "string"
                },
            }

job_schema = {
    "id": "/",
    "type": "object",
    "properties": {
        "job_action": {
            "id": "job_action",
            "type": "object",
            "properties": job_action_properties,
            "additionalProperties": True,
            "required": [
                "action"
            ]
        },
        "job_schedule": {
            "id": "job_schedule",
            "type": "object",
            "properties": job_schedule_properties,
            "additionalProperties": False,
        },
        "job_id": {
            "id": "job_id",
            "pattern": "^[\w-]+$",
            "type": "string"
        },
        "client_id": {
            "id": "client_id",
            "pattern": "^[\w-]+$",
            "type": "string"
        },
        "user_id": {
            "id": "user_id",
            "pattern": "^[\w-]+$",
            "type": "string"
        },
        "description": {
            "id": "description",
            "type": "string"
        }
    },
    "additionalProperties": False,
    "required": [
        "job_action",
        "job_schedule",
        "job_id",
        "client_id",
        "user_id"
    ]
}


job_patch_schema = {
    "id": "/",
    "type": "object",
    "properties": {
        "job_action": {
            "id": "job_action",
            "type": "object",
            "properties": job_action_properties,
            "additionalProperties": True
        },
        "job_schedule": {
            "id": "job_schedule",
            "type": "object",
            "properties": job_schedule_properties,
            "additionalProperties": False,
        },
        "job_id": {
            "id": "job_id",
            "type": "string"
        },
        "client_id": {
            "id": "client_id",
            "type": "string"
        },
        "user_id": {
            "id": "user_id",
            "type": "string"
        },
        "description": {
            "id": "description",
            "type": "string"
        }
    },
    "additionalProperties": False
}
