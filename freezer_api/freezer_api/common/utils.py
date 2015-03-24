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

    @staticmethod
    def un_serialize(d):
        return BackupMetadataDoc(
            user_id=d['user_id'],
            user_name=d['user_name'],
            data=d['backup_metadata'])

    @property
    def backup_set_id(self):
        return '{0}_{1}_{2}'.format(
            self.data['container'],
            self.data['host_name'],
            self.data['backup_name']
        )

    @property
    def backup_id(self):
        return '{0}_{1}_{2}'.format(
            self.backup_set_id,
            self.data['timestamp'],
            self.data['level']
        )
