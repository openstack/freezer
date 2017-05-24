# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P
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

import datetime
import fixtures
import os
import time


import mock

from mock import patch

from freezer.exceptions import utils as exception_utils
from freezer.openstack import osclients
from freezer.tests import commons
from freezer.utils import utils


class TestUtils(commons.FreezerBaseTestCase):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_create_dir(self):
        dir1 = '/tmp'
        dir2 = '/tmp/testnoexistent1234'
        dir3 = '~'
        assert utils.create_dir(dir1) is None
        assert utils.create_dir(dir2) is None
        os.rmdir(dir2)
        assert utils.create_dir(dir3) is None

    # def test_get_vol_fs_type(self):
    #     self.assertRaises(Exception, utils.get_vol_fs_type, "test")
    #
    #     fakeos = Os()
    #     os.path.exists = fakeos.exists
    #     self.assertRaises(Exception, utils.get_vol_fs_type, "test")
    #
    #     fakere = FakeRe()
    #     re.search = fakere.search
    #     assert type(utils.get_vol_fs_type("test")) is str
    #
    # def test_get_mount_from_path(self):
    #     dir1 = '/tmp'
    #     dir2 = '/tmp/nonexistentpathasdf'
    #     assert type(utils.get_mount_from_path(dir1)[0]) is str
    #     assert type(utils.get_mount_from_path(dir1)[1]) is str
    #     self.assertRaises(Exception, utils.get_mount_from_path, dir2)
    #
    #     pytest.raises(Exception, utils.get_mount_from_path, dir2)

    def test_human2bytes(self):
        assert utils.human2bytes('0 B') == 0
        assert utils.human2bytes('1 K') == 1024
        assert utils.human2bytes('1 Gi') == 1073741824
        assert utils.human2bytes('1 tera') == 1099511627776
        assert utils.human2bytes('0.5kilo') == 512
        assert utils.human2bytes('0.1  byte') == 0
        assert utils.human2bytes('1 k') == 1024
        assert utils.human2bytes("1000") == 1000
        self.assertRaises(ValueError, utils.human2bytes, '12 foo')

    def test_OpenstackOptions_creation_success(self):
        class FreezerOpts(object):
            def __init__(self, opts):
                self.__dict__.update(opts)

        env_dict = dict(OS_USERNAME='testusername',
                        OS_TENANT_NAME='testtenantename',
                        OS_AUTH_URL='testauthurl',
                        OS_PASSWORD='testpassword',
                        OS_REGION_NAME='testregion',
                        OS_TENANT_ID='0123456789',
                        OS_AUTH_VERSION='2.0')
        options = osclients.OpenstackOpts.create_from_dict(
            env_dict).get_opts_dicts()
        options = FreezerOpts(options)
        assert options.username == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']
        assert options.region_name == env_dict['OS_REGION_NAME']
        assert options.tenant_id == env_dict['OS_TENANT_ID']

        env_dict = dict(OS_USERNAME='testusername',
                        OS_TENANT_NAME='testtenantename',
                        OS_AUTH_URL='testauthurl',
                        OS_PASSWORD='testpassword',
                        OS_AUTH_VERSION='2.0')
        options = osclients.OpenstackOpts.create_from_dict(
            env_dict).get_opts_dicts()
        options = FreezerOpts(options)
        assert options.username == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']

    def test_date_to_timestamp(self):
        # ensure that timestamp is check with appropriate timezone offset
        assert (1417649003 + time.timezone) == utils.date_to_timestamp(
            "2014-12-03T23:23:23")

    def prepare_env(self):
        self.useFixture(fixtures.EnvironmentVariable(
            "HTTP_PROXY", 'http://proxy.original.domain:8080'))
        self.useFixture(fixtures.EnvironmentVariable("HTTPS_PROXY"))

    def test_alter_proxy(self):
        """
        Testing freezer.arguments.alter_proxy function does it set
        HTTP_PROXY and HTTPS_PROXY when 'proxy' key in its dictionary
        """
        # Test wrong proxy value
        self.assertRaises(Exception, utils.alter_proxy, 'boohoo')  # noqa

        # Test when there is proxy value passed
        self.prepare_env()
        test_proxy = 'http://proxy.alternative.domain:8888'
        utils.alter_proxy(test_proxy)
        assert os.environ["HTTP_PROXY"] == test_proxy
        assert os.environ["HTTPS_PROXY"] == test_proxy

    def test_exclude_path(self):
        assert utils.exclude_path('./dir/file', 'file') is True
        assert utils.exclude_path('./dir/file', '*le') is True
        assert utils.exclude_path('./dir/file', 'fi*') is True
        assert utils.exclude_path('./dir/file', '*fi*') is True
        assert utils.exclude_path('./dir/file', 'dir') is True
        assert utils.exclude_path('./dir/file', 'di*') is True
        assert utils.exclude_path('./aaa/bbb/ccc', '*bb') is True
        assert utils.exclude_path('./aaa/bbb/ccc', 'bb') is False
        assert utils.exclude_path('./a/b', 'c') is False
        assert utils.exclude_path('./a/b/c', '') is False

    @patch('freezer.utils.utils.os.walk')
    @patch('freezer.utils.utils.os.chdir')
    @patch('freezer.utils.utils.os.path.isfile')
    def test_walk_path_dir(self, mock_isfile, mock_chdir, mock_walk):
        mock_isfile.return_value = False
        mock_chdir.return_value = None
        mock_walk.return_value = [('.', ['d1', 'd2'], ['f1', 'f2']),
                                  ('./d1', [], ['f3']), ('./d2', [], []), ]
        expected = ['.', './f1', './f2', './d1', './d1/f3', './d2']
        files = []
        count = utils.walk_path('root', '', False, self.callback, files=files)
        for i in range(len(files)):
            assert expected[i] == files[i]
        assert count is len(files)

    @patch('freezer.utils.utils.os.path.isfile')
    def test_walk_path_file(self, mock_isfile):
        mock_isfile.return_value = True
        count = utils.walk_path('root', '', False, self.callback)
        assert count is 1

    def callback(self, filepath='', files=[]):
        files.append(filepath)


class TestDateTime(object):
    def setup(self):
        d = datetime.datetime(2015, 3, 7, 17, 47, 44, 716799)
        self.datetime = utils.DateTime(d)

    def test_factory(self):
        new_time = utils.DateTime.now()
        assert isinstance(new_time, utils.DateTime)

    def test_timestamp(self):
        # ensure that timestamp is check with appropriate timezone offset
        assert (1425750464 + time.timezone) == self.datetime.timestamp

    def test_repr(self):
        assert '2015-03-07 17:47:44' == '{}'.format(self.datetime)

    def test_initialize_int(self):
        d = utils.DateTime(1425750464)
        assert 1425750464 == d.timestamp
        # ensure that time is check with appropriate timezone offset
        t = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(
                (time.mktime(
                    time.strptime("2015-03-07 17:47:44",
                                  "%Y-%m-%d %H:%M:%S"))) - time.timezone))
        assert t == '{}'.format(d)

    def test_initialize_string(self):
        d = utils.DateTime('2015-03-07T17:47:44')
        # ensure that timestamp is check with appropriate timezone offset
        assert (1425750464 + time.timezone) == d.timestamp
        assert '2015-03-07 17:47:44' == '{}'.format(d)

    def test_sub(self):
        d2 = datetime.datetime(2015, 3, 7, 18, 18, 38, 508411)
        ts2 = utils.DateTime(d2)
        assert '0:30:53.791612' == '{}'.format(ts2 - self.datetime)

    def test_wait_for_positive(self):
        condition = mock.MagicMock(side_effect=[False, False, True, True])
        utils.wait_for(condition, 0.1, 1)
        self.assertEqual(3, condition.called)

    def test_wait_for_negative(self):
        condition = mock.MagicMock(side_effect=[False, False, False])
        self.assertRaises(exception_utils.TimeoutException,
                          utils.wait_for(condition, 0.1, 0.2))
