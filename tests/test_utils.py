#!/usr/bin/env python

from freezer.utils import (
    create_dir, get_vol_fs_type,
    get_mount_from_path, human2bytes, DateTime, date_to_timestamp)

import pytest
import datetime
from commons import *


class TestUtils:

    def test_create_dir(self, monkeypatch):

        dir1 = '/tmp'
        dir2 = '/tmp/testnoexistent1234'
        dir3 = '~'
        fakeos = Os()

        assert create_dir(dir1) is None
        assert create_dir(dir2) is None
        os.rmdir(dir2)
        assert create_dir(dir3) is None
        monkeypatch.setattr(os, 'makedirs', fakeos.makedirs2)
        pytest.raises(Exception, create_dir, dir2)

    def test_get_vol_fs_type(self, monkeypatch):

        backup_opt = BackupOpt1()
        pytest.raises(Exception, get_vol_fs_type, backup_opt)

        fakeos = Os()
        monkeypatch.setattr(os.path, 'exists', fakeos.exists)
        #fakesubprocess = FakeSubProcess()
        pytest.raises(Exception, get_vol_fs_type, backup_opt)

        fakere = FakeRe()
        monkeypatch.setattr(re, 'search', fakere.search)
        assert type(get_vol_fs_type(backup_opt)) is str

    def test_get_mount_from_path(self):
        dir1 = '/tmp'
        dir2 = '/tmp/nonexistentpathasdf'
        assert type(get_mount_from_path(dir1)[0]) is str
        assert type(get_mount_from_path(dir1)[1]) is str
        pytest.raises(Exception, get_mount_from_path, dir2)

    def test_human2bytes(self):
        assert human2bytes('0 B') == 0
        assert human2bytes('1 K') == 1024
        assert human2bytes('1 Gi') == 1073741824
        assert human2bytes('1 tera') == 1099511627776
        assert human2bytes('0.5kilo') == 512
        assert human2bytes('0.1  byte') == 0
        assert human2bytes('1 k') == 1024
        assert human2bytes("1000") == 1000
        pytest.raises(ValueError, human2bytes, '12 foo')

    def test_OpenstackOptions_creation_success(self):
        env_dict = dict(OS_USERNAME='testusername', OS_TENANT_NAME='testtenantename', OS_AUTH_URL='testauthurl',
                        OS_PASSWORD='testpassword', OS_REGION_NAME='testregion', OS_TENANT_ID='0123456789')
        options = OpenstackOptions.create_from_dict(env_dict)
        assert options.user_name == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']
        assert options.region_name == env_dict['OS_REGION_NAME']
        assert options.tenant_id == env_dict['OS_TENANT_ID']

        env_dict= dict(OS_USERNAME='testusername', OS_TENANT_NAME='testtenantename', OS_AUTH_URL='testauthurl',
                       OS_PASSWORD='testpassword')
        options = OpenstackOptions.create_from_dict(env_dict)
        assert options.user_name == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']
        assert options.region_name is None
        assert options.tenant_id is None

    def test_date_to_timestamp(self):
        #ensure that timestamp is check with appropriate timezone offset
        assert (1417649003+time.timezone) == date_to_timestamp("2014-12-03T23:23:23")


class TestDateTime:
    def setup(self):
        d = datetime.datetime(2015, 3, 7, 17, 47, 44, 716799)
        self.datetime = DateTime(d)

    def test_factory(self):
        new_time = DateTime.now()
        assert isinstance(new_time, DateTime)

    def test_timestamp(self):
        #ensure that timestamp is check with appropriate timezone offset
        assert (1425750464+time.timezone) == self.datetime.timestamp

    def test_repr(self):
        assert '2015-03-07 17:47:44' == '{}'.format(self.datetime)

    def test_initialize_int(self):
        d = DateTime(1425750464)
        assert 1425750464 == d.timestamp
        #ensure that time is check with appropriate timezone offset
        t = time.strftime("%Y-%m-%d %H:%M:%S", 
              time.localtime((time.mktime(time.strptime("2015-03-07 17:47:44", 
                                                    "%Y-%m-%d %H:%M:%S")))-time.timezone))
        assert t == '{}'.format(d)

    def test_initialize_string(self):
        d = DateTime('2015-03-07T17:47:44')
        assert 1425750464        #ensure that timestamp is check with appropriate timezone offset
        assert (1425750464+time.timezone) == d.timestamp
        assert '2015-03-07 17:47:44' == '{}'.format(d)

    def test_sub(self):
        d2 = datetime.datetime(2015, 3, 7, 18, 18, 38, 508411)
        ts2 = DateTime(d2)
        assert '0:30:53.791612' == '{}'.format(ts2 - self.datetime)
