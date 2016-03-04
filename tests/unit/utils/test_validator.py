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

from freezer.utils import validator
from freezer.utils import utils

class TestValidator(unittest.TestCase):
    def test_pass(self):
        bunch = utils.Bunch()
        validator.validate(bunch)

    def test_no_increment(self):
        bunch = utils.Bunch(no_incremental=True, max_level=10)
        self.assertRaises(Exception, validator.validate, bunch)

    def test_restore_without_path(self):
        bunch = utils.Bunch(action="restore")
        self.assertRaises(Exception, validator.validate, bunch)

    def test_restore_with_path(self):
        bunch = utils.Bunch(action="restore", restore_abs_path="/tmp")
        validator.validate(bunch)

    def test_backup_with_restore_path(self):
        bunch = utils.Bunch(action="backup", restore_abs_path="/tmp")
        self.assertRaises(Exception, validator.validate, bunch)

    def test_ssh(self):
        bunch = utils.Bunch(storage="ssh", ssh_key="key", ssh_username="name",
                            ssh_host="localhost")
        validator.validate(bunch)

    def test_ssh_raises(self):
        bunch = utils.Bunch(storage="ssh", ssh_key="key", ssh_username="name")
        self.assertRaises(Exception, validator.validate, bunch)
        bunch = utils.Bunch(storage="ssh", ssh_key="key", ssh_host="localhost")
        self.assertRaises(Exception, validator.validate, bunch)
        bunch = utils.Bunch(storage="ssh", ssh_username="name",
                            ssh_host="localhost")
        self.assertRaises(Exception, validator.validate, bunch)
