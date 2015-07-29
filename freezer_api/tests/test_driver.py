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
from mock import patch

from oslo_config import cfg

from freezer_api.common.exceptions import *
from freezer_api.storage import driver, elastic


class TestStorageDriver(unittest.TestCase):

    @patch('freezer_api.storage.elastic.logging')
    def test_get_db_raises_when_db_not_supported(self, mock_logging):
        cfg.CONF.storage.db = 'nodb'
        self.assertRaises(Exception, driver.get_db)

    @patch('freezer_api.storage.elastic.logging')
    def test_get_db_elastic(self, mock_logging):
        cfg.CONF.storage.db = 'elasticsearch'
        db = driver.get_db()
        self.assertIsInstance(db, elastic.ElasticSearchEngine)
