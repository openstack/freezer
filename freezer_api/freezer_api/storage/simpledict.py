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

import logging
from freezer_api.common.utils import BackupMetadataDoc
from freezer_api.common import exceptions


class SimpleDictStorageEngine(object):

    def __init__(self):
        self._map = {}

    def get_backup(self, user_id, backup_id):
        try:
            backup_data = self._map[(user_id, backup_id)]
        except:
            raise exceptions.ObjectNotFound(
                message='Requested backup data not found: {0}'.
                format(backup_id),
                resp_body={'backup_id': backup_id})
        return backup_data

    def get_backup_list(self, user_id):
        backup_list = []
        for (key, backup_data) in self._map.iteritems():
            if key[0] == user_id:
                backup_list.append(backup_data)
        return backup_list

    def add_backup(self, user_id, user_name, data):
        backup_metadata_doc = BackupMetadataDoc(user_id, user_name, data)
        if not backup_metadata_doc.is_valid():
            raise exceptions.BadDataFormat(message='Bad Data Format')
        backup_id = backup_metadata_doc.backup_id
        if (user_id, backup_id) in self._map:
            raise exceptions.DocumentExists(
                message='Backup data already existing ({0})'.format(backup_id),
                resp_body={'backup_id': backup_id})
        self._map[(user_id, backup_id)] = backup_metadata_doc.serialize()
        logging.info('Adding backup data with backup_id {0}'.format(backup_id))
        return backup_id

    def delete_backup(self, user_id, backup_id):
        try:
            self._map.pop((user_id, backup_id))
        except KeyError:
            raise exceptions.ObjectNotFound(
                message='Object to remove not found: {0}'.format(backup_id),
                resp_body={'backup_id': backup_id})
        return backup_id
