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
import subprocess

import tempest.test

class BaseFreezerTest(tempest.test.BaseTestCase):

    credentials = ['primary']

    def __init__(self, *args, **kwargs):

        super(BaseFreezerTest, self).__init__(*args, **kwargs)


    def setUp(self):
        super(BaseFreezerTest, self).setUp()

        self.get_environ()

    def tearDown(self):

        super(BaseFreezerTest, self).tearDown()

    @classmethod
    def get_auth_url(cls):
        return cls.os_primary.auth_provider.auth_client.auth_url[:-len('/tokens')]

    @classmethod
    def setup_clients(cls):
        super(BaseFreezerTest, cls).setup_clients()
        cls.get_environ()

    @classmethod
    def get_environ(cls):
        os.environ['OS_PASSWORD'] = cls.os_primary.credentials.password
        os.environ['OS_USERNAME'] = cls.os_primary.credentials.username
        os.environ['OS_PROJECT_NAME'] = cls.os_primary.credentials.tenant_name
        os.environ['OS_TENANT_NAME'] = cls.os_primary.credentials.tenant_name

        # Allow developers to set OS_AUTH_URL when developing so that
        # Keystone may be on a host other than localhost.
        if not 'OS_AUTH_URL' in os.environ:
                os.environ['OS_AUTH_URL'] = cls.get_auth_url()

        # Mac OS X uses gtar located in /usr/local/bin
        os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']

        return os.environ


    def run_subprocess(self, sub_process_args, fail_message):

        proc = subprocess.Popen(sub_process_args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=self.environ, shell=False)

        out, err = proc.communicate()

        self.assertEqual(0, proc.returncode,
                         fail_message + " Output: {0}. "
                                        "Error: {1}".format(out, err))

        self.assertEqual('', out,
                       fail_message + " Output: {0}. "
                                      "Error: {1}".format(out, err))

        self.assertEqual('', err,
                         fail_message + " Output: {0}. "
                                        "Error: {1}".format(out, err))
