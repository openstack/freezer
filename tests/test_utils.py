#!/usr/bin/env python

from freezer.utils import (
    gen_manifest_meta, validate_all_args,
    sort_backup_list, create_dir, get_vol_fs_type,
    get_mount_from_path, human2bytes, DateTime, date_to_timestamp)

from freezer.swift import (get_match_backup,
                           get_newest_backup,get_rel_oldest_backup,
                           eval_restart_backup, set_backup_level,
                           check_backup_and_tar_meta_existence)
from freezer import swift
import pytest
import datetime
from commons import *


class TestUtils:

    def test_gen_manifest_meta(self):

        backup_opt = BackupOpt1()
        manifest_meta = {}

        gen_manifest_meta(
            backup_opt, manifest_meta, meta_data_backup_file='testfile')

        manifest_meta['x-object-meta-tar-meta-obj-name'] = 'testtar'
        gen_manifest_meta(
            backup_opt, manifest_meta, meta_data_backup_file='testfile')
        del manifest_meta['x-object-meta-tar-meta-obj-name']

        manifest_meta['x-object-meta-tar-prev-meta-obj-name'] = 'testtar'
        gen_manifest_meta(
            backup_opt, manifest_meta, meta_data_backup_file='testfile')
        del manifest_meta['x-object-meta-tar-prev-meta-obj-name']

        backup_opt.__dict__['encrypt_pass_file'] = False
        gen_manifest_meta(
            backup_opt, manifest_meta, meta_data_backup_file='testfile')

    def test_validate_all_args(self):

        elements1 = ['test1', 'test2', 'test3']
        elements2 = ['test1', '', False, None]
        elements3 = None

        assert validate_all_args(elements1) is True
        assert validate_all_args(elements2) is False
        pytest.raises(Exception, validate_all_args, elements3)

    def test_sort_backup_list(self):

        sorted_backups = sort_backup_list(BackupOpt1().remote_match_backup)

        sort_params = map(
            lambda x: map(lambda y: int(y), x.rsplit('_', 2)[-2:]),
            sorted_backups)

        (max_time, max_level) = sort_params[0]

        for param in sort_params:
            (backup_time, level) = param
            assert not backup_time > max_time
            assert not (backup_time == max_time and level > max_level)
            max_time = backup_time
            max_level = level

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

    def test_get_match_backup(self):

        backup_opt = BackupOpt1()

        assert len(get_match_backup(backup_opt.backup_name,
                                    backup_opt.hostname,
                                    [{'name': 'test-hostname_test-backup-name_1234567_0'}])) > 0

    def test_get_newest_backup(self):

        # no backups
        pytest.raises(Exception, get_newest_backup, "hostname", "backup", [])

        # different hostname
        pytest.raises(Exception, get_newest_backup, "hostname", "backup",
                      ["notthesamename_backup_1234_12",
                       "tar_metadata_hostname_backup_1234_2"])

        # no tar file
        pytest.raises(Exception, get_newest_backup, "hostname", "backup",
                      ["hostname_backup_1234_2"])

        assert get_newest_backup("hostname", "backup",
                                 ["hostname_backup_1234_2", "tar_metadata_hostname_backup_1234_2"]) == \
               "hostname_backup_1234_2"

    def test_get_rel_oldest_backup(self):
        remote_rel_oldest = get_rel_oldest_backup("test-hostname",
                                                  "test-backup-name",
                                                  [{"name": "test-hostname_test-backup-name_1234569_0"}])
        assert len(remote_rel_oldest) > 0

    def test_eval_restart_backup(self, monkeypatch):

        backup_opt = BackupOpt1()
        assert eval_restart_backup(backup_opt) is False

        backup_opt.__dict__['restart_always_level'] = None
        assert eval_restart_backup(backup_opt) is False

        backup_opt = BackupOpt1()
        assert eval_restart_backup(backup_opt) is False

        backup_opt = BackupOpt1()
        fakere2 = FakeRe2()
        monkeypatch.setattr(re, 'search', fakere2.search)
        assert eval_restart_backup(backup_opt) is not None
        #pytest.raises(Exception, eval_restart_backup, backup_opt)

    def test_set_backup_level(self):

        manifest_meta = dict()
        backup_opt = BackupOpt1()
        backup_opt.__dict__['no_incremental'] = False
        manifest_meta['x-object-meta-backup-name'] = True
        manifest_meta['x-object-meta-backup-current-level'] = 1
        manifest_meta['x-object-meta-always-backup-level'] = 3
        manifest_meta['x-object-meta-restart-always-backup'] = 3

        (backup_opt, manifest_meta_dict) = set_backup_level(
            backup_opt, manifest_meta)
        assert manifest_meta['x-object-meta-backup-current-level'] is not False

        backup_opt = BackupOpt1()
        backup_opt.__dict__['no_incremental'] = False
        manifest_meta['x-object-meta-maximum-backup-level'] = 2
        (backup_opt, manifest_meta_dict) = set_backup_level(
            backup_opt, manifest_meta)
        assert manifest_meta['x-object-meta-backup-current-level'] is not False

        backup_opt = BackupOpt1()
        backup_opt.__dict__['no_incremental'] = False
        backup_opt.__dict__['curr_backup_level'] = 1
        (backup_opt, manifest_meta_dict) = set_backup_level(
            backup_opt, manifest_meta)
        assert manifest_meta['x-object-meta-backup-current-level'] is not False

        manifest_meta = dict()
        backup_opt = BackupOpt1()
        backup_opt.__dict__['no_incremental'] = False
        manifest_meta['x-object-meta-backup-name'] = False
        manifest_meta['x-object-meta-maximum-backup-level'] = 0
        manifest_meta['x-object-meta-backup-current-level'] = 1
        (backup_opt, manifest_meta) = set_backup_level(
            backup_opt, manifest_meta)
        assert manifest_meta['x-object-meta-backup-current-level'] == '0'

        manifest_meta = dict()
        backup_opt = BackupOpt1()
        backup_opt.__dict__['max_level'] = False
        backup_opt.__dict__['always_level'] = False
        (backup_opt, manifest_meta) = set_backup_level(
            backup_opt, manifest_meta)
        assert manifest_meta['x-object-meta-backup-current-level'] == '0'

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

    def test_check_backup_existance(self, monkeypatch):

        backup_opt = BackupOpt1()
        backup_opt.__dict__['backup_name'] = None
        assert type(check_backup_and_tar_meta_existence(backup_opt)) is dict

        backup_opt = BackupOpt1()
        assert type(check_backup_and_tar_meta_existence(backup_opt)) is dict

        fake_get_newest_backup = Fakeget_newest_backup()
        monkeypatch.setattr(swift, 'get_newest_backup', fake_get_newest_backup)
        assert type(check_backup_and_tar_meta_existence(backup_opt)) is dict

    def test_get_mount_from_path(self):
        dir1 = '/tmp'
        dir2 = '/tmp/nonexistentpathasdf'
        assert type(get_mount_from_path(dir1)) is str
        pytest.raises(Exception, get_mount_from_path, dir2)

    def test_human2bytes(self):
        assert human2bytes('0 B') == 0
        assert human2bytes('1 K') == 1024
        assert human2bytes('1 Gi') == 1073741824
        assert human2bytes('1 tera') == 1099511627776
        assert human2bytes('0.5kilo') == 512
        assert human2bytes('0.1  byte') == 0
        assert human2bytes('1 k') == 1024
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

    def test_OpenstackOption_creation_error_for_missing_parameter(self):
        env_dict = dict(OS_TENANT_NAME='testtenantename', OS_AUTH_URL='testauthurl', OS_PASSWORD='testpassword')
        pytest.raises(Exception, OpenstackOptions.create_from_dict, env_dict)

        env_dict = dict(OS_USERNAME='testusername', OS_AUTH_URL='testauthurl', OS_PASSWORD='testpassword')
        pytest.raises(Exception, OpenstackOptions.create_from_dict, env_dict)

        env_dict = dict(OS_USERNAME='testusername', OS_TENANT_NAME='testtenantename', OS_PASSWORD='testpassword')
        pytest.raises(Exception, OpenstackOptions.create_from_dict, env_dict)

        env_dict = dict(OS_USERNAME='testusername', OS_TENANT_NAME='testtenantename', OS_AUTH_URL='testauthurl')
        pytest.raises(Exception, OpenstackOptions.create_from_dict, env_dict)

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
