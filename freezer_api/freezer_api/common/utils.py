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

import jsonschema
import time
import uuid

import freezer_api.common.json_schemas
from freezer_api.common import exceptions as freezer_api_exc


class BackupMetadataDoc:
    """
    Wraps a backup_metadata dict and adds some utility methods,
    and fields
    """
    def __init__(self, user_id='', user_name='', data={}):
        self.user_id = user_id
        self.user_name = user_name
        self.data = data

    def is_valid(self):
        try:
            assert (self.backup_id is not '')
            assert (self.user_id is not '')
        except:
            return False
        return True

    def serialize(self):
        return {'backup_id': self.backup_id,
                'user_id': self.user_id,
                'user_name': self.user_name,
                'backup_metadata': self.data}

    @property
    def backup_set_id(self):
        return '{0}_{1}_{2}'.format(
            self.data['container'],
            self.data['hostname'],
            self.data['backup_name']
        )

    @property
    def backup_id(self):
        return '{0}_{1}_{2}'.format(
            self.backup_set_id,
            self.data['time_stamp'],
            self.data['curr_backup_level']
        )


class JobDoc:
    job_doc_validator = jsonschema.Draft4Validator(
        schema=json_schemas.job_schema)
    job_patch_validator = jsonschema.Draft4Validator(
        schema=json_schemas.job_patch_schema)

    @staticmethod
    def validate(doc):
        try:
            JobDoc.job_doc_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def validate_patch(doc):
        try:
            JobDoc.job_patch_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def create_patch(doc):
        # changes in user_id or job_id are not allowed
        doc.pop('user_id', None)
        doc.pop('job_id', None)
        JobDoc.validate_patch(doc)
        return doc

    @staticmethod
    def create(doc, user_id):
        job_schedule = doc.get('job_schedule', {})
        job_schedule.update({
            'time_created': int(time.time()),
            'time_started': -1,
            'time_ended': -1
        })
        doc.update({
            'user_id': user_id,
            'job_id': uuid.uuid4().hex,
            'job_schedule': job_schedule
        })
        JobDoc.validate(doc)
        return doc

    @staticmethod
    def update(doc, user_id, job_id):
        doc.update({
            'user_id': user_id,
            'job_id': job_id,
        })
        JobDoc.validate(doc)
        return doc


class ActionDoc:
    action_doc_validator = jsonschema.Draft4Validator(
        schema=json_schemas.action_schema)
    action_patch_validator = jsonschema.Draft4Validator(
        schema=json_schemas.action_patch_schema)

    @staticmethod
    def validate(doc):
        try:
            ActionDoc.action_doc_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def validate_patch(doc):
        try:
            ActionDoc.action_patch_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def create_patch(doc):
        # changes in user_id or action_id are not allowed
        doc.pop('user_id', None)
        doc.pop('action_id', None)
        ActionDoc.validate_patch(doc)
        return doc

    @staticmethod
    def create(doc, user_id):
        doc.update({
            'user_id': user_id,
            'action_id': uuid.uuid4().hex,
        })
        ActionDoc.validate(doc)
        return doc

    @staticmethod
    def update(doc, user_id, action_id):
        doc.update({
            'user_id': user_id,
            'action_id': action_id,
        })
        ActionDoc.validate(doc)
        return doc


class SessionDoc:
    session_doc_validator = jsonschema.Draft4Validator(
        schema=json_schemas.session_schema)
    session_patch_validator = jsonschema.Draft4Validator(
        schema=json_schemas.session_patch_schema)

    @staticmethod
    def validate(doc):
        try:
            SessionDoc.session_doc_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def validate_patch(doc):
        try:
            SessionDoc.session_patch_validator.validate(doc)
        except Exception as e:
            raise freezer_api_exc.BadDataFormat(str(e).splitlines()[0])

    @staticmethod
    def create_patch(doc):
        # changes in user_id or session_id are not allowed
        doc.pop('user_id', None)
        doc.pop('session_id', None)
        SessionDoc.validate_patch(doc)
        return doc

    @staticmethod
    def create(doc, user_id, hold_off=30):
        doc.update({
            'user_id': user_id,
            'session_id': uuid.uuid4().hex,
            'session_tag': 0,
            'status': 'active',
            'last_start': '',
            'jobs': []
        })
        doc['hold_off'] = doc.get('hold_off', hold_off)
        SessionDoc.validate(doc)
        return doc

    @staticmethod
    def update(doc, user_id, session_id):
        doc.update({
            'user_id': user_id,
            'session_id': session_id,
        })
        SessionDoc.validate(doc)
        return doc
