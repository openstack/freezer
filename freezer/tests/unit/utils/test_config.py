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

import io
import os
import tempfile
import unittest

from freezer.common import config as freezer_config
from freezer.tests import commons
from freezer.utils import config
from oslo_config import cfg

CONF = cfg.CONF


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

        fd = io.StringIO(string)
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


class TestConfigCoercion(commons.FreezerBaseTestCase):

    def setUp(self):
        super(TestConfigCoercion, self).setUp()
        self.temp_files = []

    def tearDown(self):
        for path in self.temp_files:
            try:
                os.remove(path)
            except OSError:
                pass
        super(TestConfigCoercion, self).tearDown()

    def _create_temp_config(self, content):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name

    def test_get_backup_args_coercion_falsy(self):
        log_path = self._create_temp_config("")
        config_content = """[default]
log_file = {0}
incremental = false
consistency_check = no
overwrite = 0
timeout = 120
""".format(log_path)
        config_path = self._create_temp_config(config_content)

        CONF.reset()
        freezer_config.config(args=['--config', config_path])
        backup_args = freezer_config.get_backup_args()

        self.assertIs(backup_args.incremental, False)
        self.assertIs(backup_args.consistency_check, False)
        self.assertIs(backup_args.overwrite, False)
        self.assertEqual(backup_args.timeout, 120)

    def test_get_backup_args_coercion_truthy(self):
        log_path = self._create_temp_config("")
        config_content = """[default]
log_file = {0}
incremental = true
consistency_check = yes
overwrite = 1
""".format(log_path)
        config_path = self._create_temp_config(config_content)

        CONF.reset()
        freezer_config.config(args=['--config', config_path])
        backup_args = freezer_config.get_backup_args()

        self.assertIs(backup_args.incremental, True)
        self.assertIs(backup_args.consistency_check, True)
        self.assertIs(backup_args.overwrite, True)
