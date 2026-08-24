#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest import mock

from freezer.mode import mongo


class FakeConf(object):
    hostname = 'test-host'


class TestMongoMode(unittest.TestCase):

    @mock.patch('pymongo.MongoClient')
    def test_client_uses_mongodb_uri_scheme(self, mock_client):
        """The MongoDB client must be created with a valid connection URI.

        pymongo 4.x rejects a bare "host:port" string with
        "[Errno 22] Invalid argument"; the connection string must carry the
        "mongodb://" scheme. This asserts MongoMode builds such a URI.
        """
        # isMaster must report this node as primary so __init__ succeeds.
        instance = mock_client.return_value
        instance.admin.command.return_value = {
            'me': 'test-host:27017',
            'primary': 'test-host:27017',
        }

        mongo.MongoMode(FakeConf())

        # MongoClient must be called once with a mongodb:// URI.
        mock_client.assert_called_once()
        uri = mock_client.call_args[0][0]
        self.assertTrue(
            uri.startswith('mongodb://'),
            "MongoClient must be called with a mongodb:// URI, got: "
            "{0}".format(uri))
        self.assertEqual('mongodb://test-host:27017', uri)
