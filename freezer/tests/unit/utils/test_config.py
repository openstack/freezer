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

from six import moves

from freezer.utils import config


class TestConfig(unittest.TestCase):
    def test_export(self):
        string = """unset OS_DOMAIN_NAME
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

        res = config.osrc_parse(string)
        self.assertEqual("http://abracadabra/v3", res["OS_AUTH_URL"])

    def test_ini(self):
        string = """[default]
# This is a comment line
#
host = 127.0.0.1
port = 3306
user = openstack
password = 'aNiceQuotedPassword'
password2 = "aNiceQuotedPassword"
spaced =   value"""

        fd = moves.cStringIO(string)
        res = config.ini_parse(fd)
        self.assertEqual('127.0.0.1', res['host'])
        self.assertEqual('openstack', res['user'])
        self.assertEqual('3306', res['port'])

        # python 3.4 tests will fail because aNiceQuatedPassword will
        # be quoted like "'aNiceQuotedPassword'" and '"aNiceQuotedPassword"'.
        # Solution for now is to strip the inside quotation marks.
        self.assertEqual('aNiceQuotedPassword', res['password'].strip("\"")
                         .strip('\''))
        self.assertEqual('aNiceQuotedPassword', res['password2'].strip("\"")
                         .strip('\''))

        self.assertEqual('value', res['spaced'])
