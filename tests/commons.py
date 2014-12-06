#!/usr/bin/env python

from freezer.backup import backup_mode_mysql, backup_mode_fs, backup_mode_mongo
import freezer
import swiftclient
import multiprocessing
import subprocess
import time
import os
import MySQLdb
import pymongo
import re

import __builtin__

os.environ['OS_REGION_NAME'] = 'testregion'
os.environ['OS_TENANT_ID'] = '0123456789'
os.environ['OS_PASSWORD'] = 'testpassword'
os.environ['OS_AUTH_URL'] = 'testauthurl'
os.environ['OS_USERNAME'] = 'testusername'
os.environ['OS_TENANT_NAME'] = 'testtenantename'


class FakeLogging:

    def __init__(self):
        return None

    def __call__(self, *args, **kwargs):
        return True

    @classmethod
    def logging(cls, opt1=True):
        return True

    @classmethod
    def info(cls, opt1=True):
        return True

    @classmethod
    def warning(cls, opt1=True):
        return True

    @classmethod
    def critical(cls, opt1=True):
        return True

    @classmethod
    def exception(cls, opt1=True):
        return True

    @classmethod
    def error(cls, opt1=True):
        return True


class Fakeget_newest_backup:

    def __init__(self, opt1=True):
        return None

    def __call__(self, *args, **kwargs):
        backup_opt = BackupOpt1()
        backup_opt.__dict__['remote_newest_backup'] = False
        return backup_opt


class Fakeget_rel_oldest_backup:

    def __init__(self, opt1=True):
        return None

    def __call__(self, *args, **kwargs):
        backup_opt = BackupOpt1()
        backup_opt.__dict__['remote_rel_oldest'] = False
        return backup_opt


class Fakeget_rel_oldest_backup2:

    def __init__(self, opt1=True):
        return None

    def __call__(self, *args, **kwargs):
        backup_opt = BackupOpt1()
        backup_opt.__dict__['remote_rel_oldest'] = True
        return backup_opt


class FakeDistutils:

    def __init__(self):
        return None

    class spawn:
        def __init__(self, *args, **kwargs):
            return None

        def __call__(self, *args, **kwargs):
            return self

        def find_executable(self, *args, **kwargs):
            return True


class FakeArgparse:

    def __init__(self):
        return None

    def __call__(self, prog='freezerc'):
        return self.ArgumentParser

    class ArgumentParser:

        def __init__(self, prog='freezerc'):
            return None

        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def add_argument(self, *args, **kwargs):
            self.container = 'testcontainer'
            self.hostname = 'testhostname'
            return True

        @classmethod
        def parse_args(self):
            self.hostname = None
            return self


class FakeOpen:
    def __init__(self):
        return None

    @classmethod
    def fopen(self, opt1=True, op2=True):

        #fd_open = __builtin__.open('/tmp/pytest-testopen', 'w')
        #fd_open.write('/dev/mapper/testgroup-testsnapname\n')
        #fd_open.close()
        #with __builtin__.open('/tmp/pytest-testopen', 'r') as fd_open:
        #    return fd_open
        fake_fd = [
            '/dev/mapper/testgroup-testsnapname test1 test2 test3',
            '/dev/mapjkhkper/testsdkjs-testsnaalskdjalpnme test1 test2 test3']
        return fake_fd

    @classmethod
    def close(self):
        return self

    @classmethod
    def readlines(self):
        fake_fd = []
        fake_fd.append(
            '/dev/mapper/testgroup-testsnapname test1 test2 test3')
        fake_fd.append(
            '/dev/mapjkhkper/testsdkjs-testsnaalskdjalpnme test1 test2 test3')
        return fake_fd


class FakeBackup:
    def __init__(self):
        return None

    def backup_mode_fs(opt1=True, opt2=True, opt3=True, opt4=True):
        return True


class FakeMultiProcessing:
    def __init__(self, duplex=True, maxsize=True):
        return None

    class Queue:
        def __init__(self, duplex=True):
            return None

        def put(self, opt1=dict()):
            return True

        def get(self, opt1=dict()):
            return True

        def __call__(self, duplex=True):
            return []

    class Pipe:
        def __init__(self, duplex=True):
            return None

        def send_bytes(self, opt1=True):
            return True

        def recv_bytes(self, opt1=True):
            return True

        def send(self, opt1=True):
            return True

        def recv(self, opt1=True):
            return True

        def poll(self):
            return True

        def close(self):
            return True

        def __call__(self, duplex=True):
            return [self, self]

    class Process:
        def __init__(self, target=True, args=True):
            return None

        def start(self):
            return True

        def stop(self):
            return True

        def daemon(self):
            return True

        def join(self):
            return True

    @classmethod
    def util(cls):
        return True


class FakeSubProcess:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return 'successfully removed', ''


class FakeSubProcess1:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return '', 'asdfasdf'


class FakeSubProcess2:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return '', 'already mounted'


class FakeSubProcess3:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return False, False


class FakeSubProcess4:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return '', ''


class Lvm:
    def __init__(self):
        return None

    def lvm_snap_remove(self, opt1=True):
        return True

    def lvm_eval(self, opt1=True):
        return False


class FakeSwiftClient:

    def __init__(self):
        return None

    class client:
        def __init__(self):
            return None

        class Connection:
            def __init__(self, key=True, os_options=True, auth_version=True, user=True, authurl=True, tenant_name=True, retries=True):
                return None

            def put_object(self, opt1=True, opt2=True, opt3=True, opt4=True, opt5=True, headers=True, content_length=True, content_type=True):
                return True

            def head_object(self, opt1=True, opt2=True):
                return True


class FakeRe:

    def __init__(self):
        return None

    @classmethod
    def search(self, opt1=True, opt2=True, opt3=True):
            return self

    @classmethod
    def group(self, opt1=True, opt2=True):
        if opt1 == 1:
            return 'testgroup'
        else:
            return '10'


class FakeRe2:

    def __init__(self):
        return None

    def __call__(self, *args, **kwargs):
        return None

    @classmethod
    def search(cls, opt1=True, opt2=True, opt3=True):
        return None

    @classmethod
    def group(cls, opt1=True, opt2=True):
        return None


class BackupOpt1:

    def __init__(self):
        fakeclient = FakeSwiftClient()
        fakeconnector = fakeclient.client()
        fakeswclient = fakeconnector.Connection()
        self.mysql_conf_file = '/tmp/freezer-test-conf-file'
        self.mysql_db_inst = FakeMySQLdb()
        self.lvm_auto_snap = '/dev/null'
        self.lvm_volgroup = 'testgroup'
        self.lvm_srcvol = 'testvol'
        self.lvm_dirmount= '/tmp/testdir'
        self.lvm_snapsize = '1G'
        self.lvm_snapname = 'testsnapname'
        self.lvcreate_path = 'true'
        self.lvremove_path = 'true'
        self.mode = 'mysql'
        self.bash_path = 'true'
        self.file_path = 'true'
        self.mount_path = 'true'
        self.umount_path = 'true'
        self.backup_name = 'test-backup-name'
        self.hostname = 'test-hostname'
        self.curr_backup_level = 0
        self.src_file = '/tmp'
        self.tar_path= 'true'
        self.dereference_symlink = 'true'
        self.no_incremental = 'true'
        self.exclude = 'true'
        self.encrypt_pass_file = 'true'
        self.openssl_path = 'true'
        self.always_backup_level = '0'
        self.max_backup_level = '0'
        self.remove_older_than = '0'
        self.max_seg_size = '0'
        self.time_stamp = 123456789
        self.container_segments = 'test-container-segements'
        self.container = 'test-container'
        self.workdir = '/tmp'
        self.upload = 'true'
        self.sw_connector = fakeswclient
        self.max_backup_level = '20'
        self.encrypt_pass_file = '/dev/random'
        self.always_backup_level = '20'
        self.remove_older_than = '20'
        self.restart_always_backup = 100000
        self.container_segments = 'testcontainerseg'
        self.remote_match_backup = [
            'test-hostname_test-backup-name_1234567_0',
            'test-hostname_test-backup-name_1234567_1',
            'test-hostname_test-backup-name_1234567_2']
        self.remote_obj_list = [
            {'name' : 'test-hostname_test-backup-name_1234567_0'},
            {'name' : 'test-hostname_test-backup-name_1234567_1'},
            {'name' : 'test-hostname_test-backup-name_1234567_2'},
            {'fakename' : 'test-hostname_test-backup-name_1234567_2'},
            {'name' : 'test-hostname-test-backup-name-asdfa-asdfasdf'}]
        self.remote_objects = []


class FakeMySQLdb:

    def __init__(self):
        return None

    def __call__(self, *args, **kwargs):
        return self

    @classmethod
    def connect(cls, host=True, user=True, passwd=True):
            return cls

    @classmethod
    def cursor(cls):
        return cls

    @classmethod
    def execute(cls, string=str):
        return cls

    @classmethod
    def close(cls):
        return cls

    @classmethod
    def commit(cls):
        return cls

    @classmethod
    def close(cls):
        return True


class FakeMySQLdb2:

    def __init__(self):
        return None

    @classmethod
    def connect(self, host=True, user=True, passwd=True):
        raise Exception


class FakeMongoDB:

    def __init__(self, opt1=True):
        return None

    def __call__(self, opt1=True):
        return self

    class admin:
        def __init__(self):
            return None

        @classmethod
        def command(cls, opt1=True):
            return {'me': 'testnode', 'primary': 'testnode'}


class FakeMongoDB2:

    def __init__(self, opt1=True):
        return None

    def __call__(self, opt1=True):
        return self

    class admin:
        def __init__(self):
            return None

        @classmethod
        def command(cls, opt1=True):
            return {'me': 'testnode', 'primary': 'testanothernode'}


class Os:
    def __init__(self, directory=True):
        return None

    @classmethod
    def __call__(cls, *args, **kwargs):
        return cls

    @classmethod
    def makedirs(cls, directory=True):
        return 'testdir'

    @classmethod
    def makedirs2(cls, directory=True):
        raise Exception

    @classmethod
    def exists(cls, directory=True):
        return 'testdir'

    @classmethod
    def expanduser(cls, directory=True, opt2=True):
        return 'testdir'

    @classmethod
    def isdir(cls, directory=True):
        return 'testdir'

    @classmethod
    def path(cls, directory=True):
        return True


    @classmethod
    def exists(cls, directory=True):
        return True

    @classmethod
    def isabs(cls, directory=True):
        return True

    @classmethod
    def expandvars(cls, directory=True):
        return True

    @classmethod
    def expanduser(cls, directory=True, opt2=True):
        return 'testdir'

    @classmethod
    def normcase(cls, directory=True, opt2=True):
        return 'testdir'

    @classmethod
    def abspath(cls, directory=True, opt2=True):
        return 'testdir'

    @classmethod
    def realpath(cls, directory=True, opt2=True):
        return 'testdir'

    @classmethod
    def isdir(cls, directory=True):
        return 'testdir'

    @classmethod
    def split(cls, directory=True):
        return ['/tmp', '']

    @classmethod
    def join(cls, directory1=True, directory2=True):
        return '/tmp/testdir'


class Fake_get_vol_fs_type:

    def __init__(self):
        return None


    @classmethod
    def get_vol_fs_type1(self, opt1=True):
        return 'xfs'

