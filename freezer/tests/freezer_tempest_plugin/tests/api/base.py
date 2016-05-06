# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import os

import tempest.test

class BaseFreezerTest(tempest.test.BaseTestCase):

    credentials = ['primary']

    def __init__(self, *args, **kwargs):

        super(BaseFreezerTest, self).__init__(*args, **kwargs)

    def setUp(self):

        super(BaseFreezerTest, self).setUp()

    def tearDown(self):

        super(BaseFreezerTest, self).tearDown()

    def get_environ(self):
        os.environ['OS_PASSWORD'] = self.os_primary.credentials.credentials.password
        os.environ['OS_USERNAME'] = self.os_primary.credentials.credentials.username
        os.environ['OS_PROJECT_NAME'] = self.os_primary.credentials.credentials.tenant_name
        os.environ['OS_TENANT_NAME'] = self.os_primary.credentials.credentials.tenant_name

        # Allow developers to set OS_AUTH_URL when developing so that
        # Keystone may be on a host other than localhost.
        if not 'OS_AUTH_URL' in os.environ:
                os.environ['OS_AUTH_URL'] = 'http://localhost:5000/v2.0'

        # Mac OS X uses gtar located in /usr/local/bin
        os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']

        return os.environ
