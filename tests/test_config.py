# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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

from freezer import config

class TestConfig(unittest.TestCase):
    def test_export(self):
        str = """unset OS_DOMAIN_NAME
        export OS_AUTH_URL="http://abracadabra/v3"
        export OS_PROJECT_NAME=abracadabra_project
        export OS_USERNAME=abracadabra_username
        export OS_PASSWORD=abracadabra_password
        export OS_PROJECT_DOMAIN_NAME=Default
        export OS_USER_DOMAIN_NAME=Default
        export OS_IDENTITY_API_VERSION=3
        export OS_AUTH_VERSION=3
        export OS_CACERT=/etc/ssl/certs/ca-certificates.crt
        export OS_ENDPOINT_TYPE=internalURL"""
        res = config.osrc_parse(str)
        self.assertEqual("http://abracadabra/v3", res["OS_AUTH_URL"])
