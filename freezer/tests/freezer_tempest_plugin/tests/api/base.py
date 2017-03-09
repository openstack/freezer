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

from datetime import datetime
from datetime import timedelta
import json
import os
import subprocess

from time import mktime

from tempest import test

from freezer.tests.integration.common import Temp_Tree


def resolve_paths(metadata):
    """Find all paths associated with a particular backup

    freezer-agent stores all backups in the timestamped sub-directory of the
    first backup created with a particular (name, hostname) pair, so it isn't
    possible to guess the true location of backup data. This function searches
    the backup container to find both the true parent directory and a list of
    all files associated with the given metadata.

    :param metadata: the metadata associated with the backup to resolve
    :return: a tuple containing the parent directory and a list of associated
             files, or (None, None)
    """
    base_name = '{}_{}'.format(metadata['hostname'], metadata['backup_name'])
    expected_name = '{}_{}'.format(base_name, metadata['time_stamp'])

    backup_base_path = os.path.join(metadata['container'], base_name)
    for timestamp in os.listdir(backup_base_path):
        timestamp_abs = os.path.join(backup_base_path, timestamp)

        matching = filter(lambda p: expected_name in p,
                          os.listdir(timestamp_abs))
        if matching:
            return timestamp_abs, matching

    return None, None


def mutate_timestamp(metadata, days_old):
    """Alter all timestamps of an existing backup

    Since there's no proper way to assign a timestamp to a backup, this method
    takes an existing backup and modifies all associated timestamps to make it
    otherwise indistinguishable from a backup actually created in the past.

    :param metadata: the metadata associated with the backup to mutate
    :param days_old: the age (i.e. days before now) that should be set
    """
    date = datetime.now() - timedelta(days=days_old)
    old_time_stamp = metadata['time_stamp']
    new_time_stamp = int(mktime(date.timetuple()))

    parent_dir, files = resolve_paths(metadata)
    if os.path.basename(parent_dir) == str(old_time_stamp):
        # rename the parent dir, but only if it was created for this
        # backup (the dir may contain other backups with different
        # timestamps that we shouldn't touch)
        new_path = os.path.join(os.path.dirname(parent_dir),
                                str(new_time_stamp))
        os.rename(parent_dir, new_path)
        parent_dir = new_path

    # rename each file associated with the backup, since each filename
    # contains the timestamp as well
    for old_file in files:
        new_file = old_file.replace(str(old_time_stamp), str(new_time_stamp))
        os.rename(os.path.join(parent_dir, old_file),
                  os.path.join(parent_dir, new_file))

    # update the metadata before saving to keep things consistent
    metadata['time_stamp'] = new_time_stamp


def load_metadata(path):
    """Given a metadata path, return a dict containing parsed values.

    :param path: the path to load
    :return: a metadata dict
    """
    with open(path, 'r') as f:
        return json.load(f)


def save_metadata(metadata, path):
    """Write the given metadata object to the provided path.

    :param metadata: the metadata dict to write
    :param path: the path at which to write the metadata
    """
    with open(path, 'w') as f:
        json.dump(metadata, f)


class BaseFreezerTest(test.BaseTestCase):
    credentials = ['primary']

    def __init__(self, *args, **kwargs):

        super(BaseFreezerTest, self).__init__(*args, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        super(BaseFreezerTest, self).setUp()

        self.storage = Temp_Tree()
        self.source_trees = []
        self.backup_count = 0
        self.backup_name = 'backup_test'

        self.get_environ()

    def tearDown(self):

        super(BaseFreezerTest, self).tearDown()

        for tree in self.source_trees:
            tree.cleanup()

        self.storage.cleanup()

    @classmethod
    def get_auth_url(cls):
        return cls.os_primary.auth_provider.auth_client.auth_url[:-len(
            '/auth/tokens')]

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
        os.environ['OS_PROJECT_DOMAIN_NAME'] = \
            cls.os_primary.credentials.project_domain_name
        os.environ['OS_USER_DOMAIN_NAME'] = \
            cls.os_primary.credentials.user_domain_name

        # Allow developers to set OS_AUTH_URL when developing so that
        # Keystone may be on a host other than localhost.
        if 'OS_AUTH_URL' not in os.environ:
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

        self.assertEqual('', err,
                         fail_message + " Output: {0}. "
                                        "Error: {1}".format(out, err))

    def create_local_backup(self, hostname=None, compression=None,
                            consistency_check=None, incremental=True,
                            always_level=None, restart_always_level=None,
                            max_level=None):
        """Creates a new backup with the given parameters.

        The backup will immediately be created using a randomly-generated
        source tree on the local filesystem, and will be stored in a random
        temporary directory using the 'local' storage mode. All generated data
        files will be automatically removed during `tearDown()`, though
        implementations are responsible for cleaning up any additional copies
        or restores created via other methods.

        :param hostname: if set, set `--hostname` to the given value
        :param compression: if set, set `--compression` to the given value
        :param consistency_check: if True, set `--consistency_check`
        :param incremental: if False, set `--no-incremental`
        :param always_level: sets `--always-level` to the given value
        :param restart_always_level: sets `--restart-always-level`
        :param max_level: sets `--max-level` to the given value
        :return: the path to the stored backup metadata
        """
        metadata_path = os.path.join(
            self.storage.path,
            'metadata-{}.json'.format(self.backup_count))
        self.backup_count += 1

        tree = Temp_Tree()
        tree.add_random_data()
        self.source_trees.append(tree)

        backup_args = [
            'freezer-agent',
            '--path-to-backup', tree.path,
            '--container', self.storage.path,
            '--backup-name', self.backup_name,
            '--storage', 'local',
            '--metadata-out', metadata_path,
        ]

        if hostname:
            backup_args += ['--hostname', hostname]

        if compression:
            backup_args += ['--compression', compression]

        if consistency_check:
            backup_args += ['--consistency-check']

        if incremental:
            if always_level is not None:
                backup_args += ['--always-level', str(always_level)]

            if max_level is not None:
                backup_args += ['--max-level', str(max_level)]

            if restart_always_level:
                backup_args += ['--restart-always-level',
                                str(restart_always_level)]
        else:
            backup_args += ['--no-incremental', 'NO_INCREMENTAL']

        self.run_subprocess(backup_args, 'Test backup to local storage.')

        return metadata_path

    def create_mutated_backup(self, days_old=30, **kwargs):
        """Create a local backup with a mutated timestamp

        This creates a new backup using `create_local_backup()`, modifies it
        using `mutate_timestamp()`, and then returns the resulting (loaded)
        metadata dict.

        :param days_old: the age of the backup to create
        :param kwargs: arguments to pass to `create_local_backup()`
        :return: the loaded metadata
        """
        metadata_path = self.create_local_backup(**kwargs)

        metadata = load_metadata(metadata_path)
        mutate_timestamp(metadata, days_old)
        save_metadata(metadata, metadata_path)

        return metadata
