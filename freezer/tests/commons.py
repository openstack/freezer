#!/usr/bin/env python

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

import os

from glanceclient.common import utils as glance_utils
import mock
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import testtools

from freezer.common import config
from freezer.engine.tar import tar as tar_engine
from freezer.openstack import osclients
from freezer.storage import swift

CONF = cfg.CONF
os.environ['OS_REGION_NAME'] = 'testregion'
os.environ['OS_TENANT_ID'] = '0123456789'
os.environ['OS_PASSWORD'] = 'testpassword'
os.environ['OS_AUTH_URL'] = 'http://testauthurl/v2.0'
os.environ['OS_USERNAME'] = 'testusername'
os.environ['OS_TENANT_NAME'] = 'testtenantename'


class FakeSubProcess(object):
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

    @classmethod
    def communicate_error(cls):
        return '', 'error'

    class stdin(object):
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


class FakeSubProcess3(object):
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

    class stdin(object):
        def __call__(self, *args, **kwargs):
            return self

        @classmethod
        def write(cls, *args, **kwargs):
            return True


class FakeSubProcess6(object):
    def __init__(self):
        pass

    @classmethod
    def Popen(cls, cmd=None):
        return cls

    @classmethod
    def communicate(cls):
        return 'ok', ''

    @classmethod
    def communicate_error(cls):
        return '', 'error'


class FakeIdObject(object):
    def __init__(self, id):
        self.id = id
        self.status = "available"
        self.size = 10
        self.min_disk = 10
        self.created_at = '2016-05-12T02:00:22.000000'


class FakeCinderClient(object):
    def __init__(self):
        self.volumes = FakeCinderClient.Volumes()
        self.volume_snapshots = FakeCinderClient.VolumeSnapshot
        self.backups = FakeCinderClient.Backups()
        self.restores = FakeCinderClient.Restores()

    class Backups(object):
        def __init__(self):
            pass

        def create(self, id, container, name, desription):
            pass

        def list(self, **kwargs):
            return [FakeIdObject(4)]

    class Volumes(object):
        def __init__(self):
            pass

        @staticmethod
        def get(id):
            return FakeIdObject("5")

        @staticmethod
        def create(size, snapshot_id=None, imageRef=None):
            return FakeIdObject("2")

        @staticmethod
        def upload_to_image(volume, force, image_name,
                            container_format, disk_format):
            pass

        @staticmethod
        def delete(volume):
            pass

    class VolumeSnapshot(object):
        def __init__(self):
            pass

        @staticmethod
        def create(volume_id, name, force):
            return FakeIdObject("10")

        @staticmethod
        def delete(snapshot):
            pass

    class Restores(object):
        def __init__(self):
            pass

        @staticmethod
        def restore(backup_id):
            pass


class FakeGlanceClient(object):
    def __init__(self):
        self.images = FakeGlanceClient.Images()

    class Images(object):
        def __init__(self):
            pass

        @staticmethod
        def data(image):
            return glance_utils.IterableWithLength(iter("abc"), 3)

        @staticmethod
        def delete(image):
            pass

        @staticmethod
        def create(data, container_format, disk_format):
            return FakeIdObject("10")


class FakeSwiftClient(object):
    def __init__(self):
        pass

    class client(object):
        def __init__(self):
            pass

        class Connection(object):
            def __init__(self, key=True, os_options=True, auth_version=True,
                         user=True, authurl=True, tenant_name=True,
                         retries=True, insecure=True):
                self.num_try = 0

            def put_object(self, container, obj, contents, content_length=None,
                           etag=None, chunk_size=None, content_type=None,
                           headers=None, query_string=None,
                           response_dict=None):
                return True

            def head_object(self, container_name='', object_name=''):
                if object_name == 'has_segments':
                    return {
                        'x-object-manifest': ('freezer_segments/hostname_'
                                              'backup_name_1234567890_0')}
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
                        {'bytes': 251,
                         'last_modified': '2015-03-09T10:37:01.701170',
                         'hash': '9a8cbdb30c226d11bf7849f3d48831b9',
                         'name': ('hostname_backup_name_1234567890_0/'
                                  '1234567890/67108864/00000000'),
                         'content_type': 'application/octet-stream'},
                        {'bytes': 632,
                         'last_modified': '2015-03-09T11:54:27.860730',
                         'hash': 'd657a4035d0dcc18deaf9bfd2a3d0ebf',
                         'name': ('hostname_backup_name_1234567891_1/'
                                  '1234567891/67108864/00000000'),
                         'content_type': 'application/octet-stream'}
                    ])
                elif container == "test-container" and 'path' in kwargs:
                    return ({'container_metadata': True}, [
                        {'bytes': 251,
                         'last_modified': '2015-03-09T10:37:01.701170',
                         'hash': '9a8cbdb30c226d11bf7849f3d48831b9',
                         'name': ('hostname_backup_name_1234567890_0/'
                                  '11417649003'),
                         'content_type': 'application/octet-stream'},
                        {'bytes': 632,
                         'last_modified': '2015-03-09T11:54:27.860730',
                         'hash': 'd657a4035d0dcc18deaf9bfd2a3d0ebf',
                         'name': ('hostname_backup_name_1234567891_1/'
                                  '1417649003'),
                         'content_type': 'application/octet-stream'}
                    ])
                else:
                    return [{}, []]

            def get_account(self, *args, **kwargs):
                return [{'count': 0, 'bytes': 0, 'name': '1234'},
                        {'count': 4, 'bytes': 156095, 'name': 'a1'}], \
                       [{'name': 'test-container',
                         'bytes': 200000,
                         'count': 1000},
                        {'name': 'test-container-segments',
                         'bytes': 300000,
                         'count': 656}]

            def get_object(self, *args, **kwargs):
                return [{'x-object-meta-length': "123",
                         'x-object-meta-flavor-id': "12",
                         'x-object-meta-name': "name"}, "abc"]


class BackupOpt1(object):
    def __init__(self):
        self.dereference_symlink = None
        self.mysql_conf = '/tmp/freezer-test-conf-file'
        self.backup_media = 'fs'
        self.lvm_auto_snap = '/dev/null'
        self.lvm_volgroup = 'testgroup'
        self.lvm_srcvol = 'testvol'
        self.lvm_dirmount = '/tmp/testdir'
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
        self.path_to_backup = '/tmp'
        self.tar_path = 'true'
        self.no_incremental = 'true'
        self.exclude = 'true'
        self.encrypt_pass_file = 'true'
        self.openssl_path = 'true'
        self.always_level = '0'
        self.max_level = '0'
        self.hostname_backup_name = "hostname_backup_name"
        self.remove_older_than = '0'
        self.max_segment_size = '0'
        self.time_stamp = 123456789
        self.container = 'test-container'
        self.max_level = '20'
        self.encrypt_pass_file = '/dev/random'
        self.always_level = '20'
        self.overwrite = False
        self.remove_from_date = '2014-12-03T23:23:23'
        self.restart_always_level = 100000
        self.restore_abs_path = '/tmp'
        self.restore_from_date = '2014-12-03T23:23:23'
        self.restore_from_host = 'test-hostname'
        self.action = 'info'
        self.shadow = ''
        self.windows_volume = ''
        self.insecure = True
        self.os_auth_ver = 2
        self.dry_run = False
        self.upload_limit = -1
        self.download_limit = -1
        self.sql_server_instance = 'Sql Server'
        self.cinder_vol_id = ''
        self.cindernative_vol_id = ''
        self.cindernative_backup_id = ''
        self.nova_inst_id = ''
        self.lvm_snapperm = 'ro'

        self.compression = 'gzip'
        self.storage = mock.MagicMock()
        self.engine = mock.MagicMock()
        opts = osclients.OpenstackOpts.create_from_env().get_opts_dicts()
        self.client_manager = osclients.OSClientManager(**opts)
        self.client_manager.get_swift = mock.Mock(
            return_value=FakeSwiftClient().client.Connection())
        self.client_manager.create_swift = self.client_manager.get_swift
        self.storage = swift.SwiftStorage(self.client_manager,
                                          self.container,
                                          self.max_segment_size)
        self.engine = tar_engine.TarEngine(
            self.compression, self.dereference_symlink,
            self.exclude, self.storage, 1000, False)
        self.client_manager.get_glance = mock.Mock(
            return_value=FakeGlanceClient())
        self.client_manager.get_cinder = mock.Mock(
            return_value=FakeCinderClient())
        nova_client = mock.MagicMock()

        self.client_manager.get_nova = mock.Mock(return_value=nova_client)

        self.command = ''


class Os(object):
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
    def notexists(cls, directory=True):
        return False

    @classmethod
    def isabs(cls, directory=True):
        return True

    @classmethod
    def expandvars(cls, directory=True):
        return True

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
    def isfile(cls, directory=True):
        return True

    @classmethod
    def split(cls, directory=True):
        return ['/tmp', '']

    @classmethod
    def join(cls, directory1=True, directory2=True):
        return '/tmp/testdir'

    @classmethod
    def rmdir(cls, directory1=True):
        return True

    @classmethod
    def chdir(cls, directory1=True):
        return True

    @classmethod
    def chdir2(cls, directory1=True):
        raise Exception


class FakeDisableFileSystemRedirection(object):
    success = True

    def __enter__(self):
        return True

    def __exit__(self, type, value, traceback):
        if self.success:
            return True


class FreezerBaseTestCase(testtools.TestCase):
    def setUp(self):
        super(FreezerBaseTestCase, self).setUp()

        self._config_fixture = self.useFixture(cfg_fixture.Config())
        config.config(args=[])
        self.addCleanup(CONF.reset)

    def tearDown(self):
        super(FreezerBaseTestCase, self).tearDown()
