#!/usr/bin/env python

from freezer.backup import backup_mode_mysql, backup_mode_fs, backup_mode_mongo
import freezer
import swiftclient
import multiprocessing
import subprocess
import time
import os
import pymysql as MySQLdb
import pymongo
import re
from collections import OrderedDict
import __builtin__

os.environ['OS_REGION_NAME'] = 'testregion'
os.environ['OS_TENANT_ID'] = '0123456789'
os.environ['OS_PASSWORD'] = 'testpassword'
os.environ['OS_AUTH_URL'] = 'testauthurl'
os.environ['OS_USERNAME'] = 'testusername'
os.environ['OS_TENANT_NAME'] = 'testtenantename'


class FakeTime:

    def __init__(self):
        return None

    def sleep(self, *args):
        return True


class FakeValidate:

    def __init__(self):
        return None

    def validate_all_args_false(self, *args, **kwargs):
        return False

    def validate_any_args_false(self, *args, **kwargs):
        return False


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
            self.proxy = False
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

    def fake_backup_mode_fs(self, *args, **kwargs):
        return True

    def fake_backup_mode_mongo(self, *args, **kwargs):
        return True

    def fake_backup_mode_mysql(self, *args, **kwargs):
        return True


class FakeMultiProcessing:
    def __init__(self, *args, **kwargs):
        return None

    class Queue:
        def __init__(self):
            return None

        def put(self, opt1=dict()):
            return True

        def get(self, opt1=dict()):

            return {'item': 'test-item-value'}

        def close(self):
            return True

        def __call__(self, *args, **kwargs):
            return self

    class Pipe:
        def __init__(self, duplex=True):
            return None

        def send_bytes(self, opt1=True):
            return True

        def recv_bytes(self, opt1=True):
            raise EOFError

        def send(self, opt1=True):
            return True

        def recv(self, opt1=True):
            raise EOFError

        def poll(self):
            return True

        def close(self):
            return True

        def __call__(self, duplex=True):
            return [self, self]

    class Process:
        def __init__(self, target=True, args=True):
            self.exitcode = 0
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


class FakeMultiProcessing1:
    def __init__(self, duplex=True, maxsize=True):
        return None

    class Queue:
        def __init__(self, duplex=True, maxsize=2):
            return None

        def put(self, opt1=dict()):
            return False

        def get(self, opt1=dict()):

            return {'item': 'test-item-value'}

        def __call__(self, duplex=True):
            return []

    class Pipe:
        def __init__(self, duplex=True):
            return None

        def send_bytes(self, opt1=True):
            return False

        def recv_bytes(self, opt1=True):
            raise EOFError

        def send(self, opt1=True):
            return False

        def recv(self, opt1=True):
            raise EOFError

        def poll(self):
            return False

        def close(self):
            return False

        def __call__(self, duplex=True):
            return [self, self]

    class Process:
        def __init__(self, target=True, args=True):
            self.exitcode = 1
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
            stderr=True, shell=True, executable=True, env={},
            bufsize=4096):
        return None

    stdout = ['abcd', 'ehfg']

    @classmethod
    def Popen(cls):
        return cls

    @classmethod
    def communicate(cls):
        return 'successfully removed', ''

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


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

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


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

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


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

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


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

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


class FakeSubProcess5:
    def __init__(self, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return None

    @classmethod
    def Popen(cls, opt1=True, stdin=True, stdout=True,
            stderr=True, shell=True, executable=True):
        return cls

    @classmethod
    def communicate(cls):
        return 'error', 'error'

    class stdin:
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


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
            def __init__(self, key=True, os_options=True, auth_version=True, user=True, authurl=True, tenant_name=True, retries=True, insecure=True):
                self.num_try = 0
                return None

            def put_object(self, opt1=True, opt2=True, opt3=True, opt4=True, opt5=True, headers=True, content_length=True, content_type=True):
                return True

            def head_object(self, container_name='', object_name=''):
                if object_name == 'has_segments':
                    return {'x-object-manifest': 'freezer_segments/hostname_backup_name_1234567890_0'}
                else:
                    return {}

            def put_container(self, container=True):
                return True

            def delete_object(self, container_name='', object_name=''):
                if self.num_try > 0:
                    self.num_try -= 1
                    raise Exception("test num_try {0}".format(self.num_try))
                else:
                    return True

            def get_container(self, container, *args, **kwargs):
                if container == 'freezer_segments':
                    return ({'container_metadata': True}, [
                        {'bytes': 251, 'last_modified': '2015-03-09T10:37:01.701170', 'hash': '9a8cbdb30c226d11bf7849f3d48831b9', 'name': 'hostname_backup_name_1234567890_0/1234567890/67108864/00000000', 'content_type': 'application/octet-stream'},
                        {'bytes': 632, 'last_modified': '2015-03-09T11:54:27.860730', 'hash': 'd657a4035d0dcc18deaf9bfd2a3d0ebf', 'name': 'hostname_backup_name_1234567891_1/1234567891/67108864/00000000', 'content_type': 'application/octet-stream'}
                    ])
                else:
                    return [{}, []]

            def get_account(self, *args, **kwargs):
                return True, [{'name': 'test-container'}, {'name': 'test-container-segments'}]

            def get_object(self, *args, **kwargs):
                return ['abcdef', 'hijlmno']


class FakeSwiftClient1:

    def __init__(self):
        return None

    class client:
        def __init__(self):
            return None

        class Connection:
            def __init__(self, key=True, os_options=True, auth_version=True, user=True, authurl=True, tenant_name=True, retries=True, insecure=True):
                return None

            def put_object(self, opt1=True, opt2=True, opt3=True, opt4=True, opt5=True, headers=True, content_length=True, content_type=True):
                raise Exception

            def head_object(self, opt1=True, opt2=True):
                raise Exception

            def put_container(self, container=True):
                raise Exception

            def delete_object(self):
                raise Exception

            def get_container(self, *args, **kwargs):
                raise Exception

            def get_account(self, *args, **kwargs):
                raise Exception


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
        self.tar_path = 'true'
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
        self.container_segments = 'test-container-segments'
        self.container = 'test-container'
        self.workdir = '/tmp'
        self.upload = 'true'
        self.sw_connector = fakeswclient
        self.max_backup_level = '20'
        self.encrypt_pass_file = '/dev/random'
        self.always_backup_level = '20'
        self.remove_from_date = '2014-12-03T23:23:23'
        self.restart_always_backup = 100000
        self.remote_match_backup = [
            'test-hostname_test-backup-name_1234567_0',
            'test-hostname_test-backup-name_aaaaa__a',
            #'test-hostname_test-backup-name_9999999999999999999999999999999_0',
            'test-hostname_test-backup-name_1234568_1',
            'test-hostname_test-backup-name_1234569_2',
            'tar_metadata_test-hostname_test-backup-name_1234569_2',
            'tar_metadata_test-hostname_test-backup-name_1234568_1',
            'tar_metadata_test-hostname_test-backup-name_1234567_0']
        self.remote_obj_list = [
            {'name': 'test-hostname_test-backup-name_1234567_0',
                'last_modified': 'testdate'},
            {'name': 'test-hostname_test-backup-name_1234567_1',
                'last_modified': 'testdate'},
            {'name': 'test-hostname_test-backup-name_1234567_2',
                'last_modified': 'testdate'},
            {'name': 'tar_metadata_test-hostname_test-backup-name_1234567_2',
                'last_modified': 'testdate'},
            {'name': 'test-hostname-test-backup-name-asdfa-asdfasdf',
                'last_modified': 'testdate'}]
        self.remote_objects = []
        self.restore_abs_path = '/tmp'
        self.containers_list = [
            {'name' : 'testcontainer1', 'bytes' : 123423, 'count' : 10}
        ]
        self.list_container = False
        self.list_objects = False
        self.restore_from_date = '2014-12-03T23:23:23'
        self.restore_from_host = 'test-hostname'
        self.action = 'info'
        self.insecure = True
        self.auth_version = 2
        self.dry_run = False

class FakeMySQLdb:

    def __init__(self):
        return None

    def __call__(self, *args, **kwargs):
        return self

    @classmethod
    def connect(cls, host=True, user=True, passwd=True, port=True):
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
    def connect(self, host=True, user=True, passwd=True, port=True):
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
    def basename(cls, directory=True):
        return '/tmp'

    @classmethod
    def remove(cls, directory=True):
        True

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
    def islink(cls, file=True):
        return True

    @classmethod
    def path(cls, directory=True):
        return True

    @classmethod
    def copy(cls):
        return {}

    @classmethod
    def environ(cls, copy):
        return cls

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


class Os1(Os):
    @classmethod
    def exists(cls, directory=True):
        return False


class Fake_get_vol_fs_type:

    def __init__(self):
        return None

    @classmethod
    def get_vol_fs_type1(self, opt1=True):
        return 'xfs'


def fake_get_match_backup(self, backup_opt):
    #backup_opt = BackupOpt1()
    backup_opt.remote_match_backup = None
    return backup_opt


def fake_restore_fs_sort_obj(*args, **kwargs):
    return True


class FakeSwift:

    def __init__(self):
        return None

    def fake_get_containers_list(self, backup_opt):
        return backup_opt

    def fake_get_containers_list1(self, backup_opt):
        return backup_opt

    def fake_get_containers_list2(self, backup_opt):
        backup_opt.list_container = None
        backup_opt.list_objects = None
        return backup_opt

    def fake_get_client(self, backup_opt):
        return backup_opt

    def fake_show_containers(self, backup_opt):
        return True

    def fake_show_objects(self, backup_opt):
        return True

    def fake_check_container_existance(self, *args, **kwargs):
        return {'main_container': True, 'container_segments': True}

    def fake_check_container_existance1(self, *args, **kwargs):
        return {'main_container': False, 'container_segments': False}

    def fake_get_containers_list3(self, backup_opt):
        return backup_opt

    def fake_get_containers_list4(self, backup_opt):
        backup_opt.containers_list = []
        return backup_opt

    def fake_get_container_content(self, backup_opt):
        return backup_opt

    def remove_obj_older_than(self, backup_opt):
        return backup_opt

class FakeRestore:

    def __init__(self):
        return None

    def fake_restore_fs(self, *args, **kwargs):
        return True


class FakeUtils:

    def __init__(self):
        return None

    def fake_set_backup_level(self,backup_opt, manifest_meta):
        return backup_opt, manifest_meta

    def fake_set_backup_level_fs(self, backup_opt, manifest_meta):
        #backup_opt = BackupOpt1()
        manifest_meta = {}
        backup_opt.mode = 'fs'
        return backup_opt, manifest_meta

    def fake_set_backup_level_mongo(self, backup_opt, manifest_meta):
        #backup_opt = BackupOpt1()
        manifest_meta = {}
        backup_opt.mode = 'mongo'
        return backup_opt, manifest_meta

    def fake_set_backup_level_mysql(self, backup_opt, manifest_meta):
        #backup_opt = BackupOpt1()
        manifest_meta = {}
        backup_opt.mode = 'mysql'
        return backup_opt, manifest_meta

    def fake_set_backup_level_none(self, backup_opt, manifest_meta):
        #backup_opt = BackupOpt1()
        manifest_meta = {}
        backup_opt.mode = None
        return backup_opt, manifest_meta


class FakeJob:
    def __init__(self, conf_dict):
        self.conf = conf_dict

    def execute(self):
        return

def fake_create_job(conf):
    return FakeJob(conf)
