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

import hashlib
import json
import os
import shutil
import tempfile
import time

from tempest.lib.cli import base as cli_base
from tempest.lib.cli import output_parser

from freezer.tests.freezer_tempest_plugin.tests.api import base

JOB_TABLE_RESULT_COLUMN = 3


class BaseFreezerCliTest(base.BaseFreezerTest):
    """Base test case class for all Freezer API tests."""

    credentials = ['primary']

    @classmethod
    def setup_clients(cls):
        super(BaseFreezerCliTest, cls).setup_clients()

        cls.cli = CLIClientWithFreezer(
            username=cls.os_primary.credentials.username,
            # fails if the password contains an unescaped $ sign
            password=cls.os_primary.credentials.password.replace('$', '$$'),
            tenant_name=cls.os_primary.credentials.tenant_name,
            uri=cls.get_auth_url(),
            cli_dir='/usr/local/bin'  # devstack default
        )
        cls.cli.cli_dir = ''

    def delete_job(self, job_id):
        self.cli.freezer_client(action='job-delete', params=job_id)

    def create_job(self, job_json):

        with tempfile.NamedTemporaryFile(delete=False) as job_file:
            job_file.write(json.dumps(job_json))
            job_file.flush()

            output = self.cli.freezer_client(
                action='job-create',
                params='--file {} --client {}'.format(job_file.name,
                                                      job_json['client_id']))
            job_id = output.split()[1]
            expected = 'Job {} created'.format(job_id)
            self.assertEqual(expected, output.strip())

            self.addCleanup(self.delete_job, job_id)

            return job_id

    def find_job_in_job_list(self, job_id):
        job_list = output_parser.table(
            self.cli.freezer_client(action='job-list', params='-C test_node'))

        for row in job_list['values']:
            if row[0].strip() == job_id.strip():
                return row

        self.fail('Could not find job: {}'.format(job_id))

    def wait_for_job_status(self, job_id, timeout=720):
        start = time.time()

        while True:
            row = self.find_job_in_job_list(job_id)

            if row[JOB_TABLE_RESULT_COLUMN]:
                return
            elif time.time() - start > timeout:
                self.fail("Status of job '{}' is '{}'."
                          .format(job_id, row[JOB_TABLE_RESULT_COLUMN]))
            else:
                time.sleep(1)

    def assertJobColumnEqual(self, job_id, column, expected):
        row = self.find_job_in_job_list(job_id)
        self.assertEqual(expected, row[column])


class CLIClientWithFreezer(cli_base.CLIClient):
    def freezer_scheduler(self, action, flags='', params='', fail_ok=False,
                          endpoint_type='publicURL', merge_stderr=False):
        """Executes freezer-scheduler command for the given action.

        :param action: the cli command to run using freezer-scheduler
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """

        flags += ' --os-endpoint-type %s' % endpoint_type
        flags += ' --os-cacert /etc/ssl/certs/ca-certificates.crt'
        flags += ' --os-project-domain-name Default'
        flags += ' --os-user-domain-name Default'

        return self.cmd_with_auth(
            'freezer-scheduler', action, flags, params, fail_ok, merge_stderr)

    def freezer_client(self, action, flags='', params='', fail_ok=False,
                       endpoint_type='publicURL', merge_stderr=True):
        flags += ' --os-endpoint-type %s' % endpoint_type
        flags += ' --os-cacert /etc/ssl/certs/ca-certificates.crt'
        flags += ' --os-project-domain-name Default'
        flags += ' --os-user-domain-name Default'
        return self.cmd_with_auth(
            'freezer', action, flags, params, fail_ok, merge_stderr)


# This class is just copied from the freezer repo. Depending on where the
# scenario tests end up we may need to refactore this.
class Temp_Tree(object):
    def __init__(self, suffix='', dir=None, create=True):
        self.create = create
        if create:
            self.path = tempfile.mkdtemp(dir=dir, prefix='__freezer_',
                                         suffix=suffix)
        else:
            self.path = dir
        self.files = []

    def __enter__(self):
        return self

    def cleanup(self):
        if self.create and self.path:
            shutil.rmtree(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def add_random_data(self, ndir=5, nfile=5, size=1024):
        """
        add some files containing randoma data

        :param ndir: number of dirs to create
        :param nfile: number of files to create in each dir
        :param size: size of files
        :return: None
        """
        for x in range(ndir):
            subdir_path = tempfile.mkdtemp(dir=self.path)
            for y in range(nfile):
                abs_pathname = self.create_file_with_random_data(
                    dir_path=subdir_path, size=size)
                rel_path_name = abs_pathname[len(self.path) + 1:]
                self.files.append(rel_path_name)

    def create_file_with_random_data(self, dir_path, size=1024):
        handle, abs_pathname = tempfile.mkstemp(dir=dir_path)
        with open(abs_pathname, 'wb') as fd:
            fd.write(os.urandom(size))
        return abs_pathname

    def get_file_hash(self, rel_filepath):
        filepath = os.path.join(self.path, rel_filepath)
        if os.path.isfile(filepath):
            return self._filehash(filepath)
        else:
            return ''

    def _filehash(self, filepath):
        """
        Get GIT style sha1 hash for a file

        :param filepath: path of file to hash
        :return: hash of the file
        """
        filesize_bytes = os.path.getsize(filepath)
        hash_obj = hashlib.sha1()
        hash_obj.update(("blob %u\0" % filesize_bytes).encode('utf-8'))
        with open(filepath, 'rb') as handle:
            hash_obj.update(handle.read())
        return hash_obj.hexdigest()

    def get_file_list(self):
        """
        walks the dir tree and creates a list of relative pathnames
        :return: list of relative file paths
        """
        self.files = []
        for root, dirs, files in os.walk(self.path):
            rel_base = root[len(self.path) + 1:]
            self.files.extend([os.path.join(rel_base, x) for x in files])
        return self.files

    def is_equal(self, other_tree):
        """
        Checks whether two dir tree contain the same files
        It checks the number of files and the hash of each file.

        NOTE: tox puts .coverage files in the temp folder (?)

        :param other_tree: dir tree to compare with
        :return: true if the dir trees contain the same files
        """
        lh_files = [x for x in sorted(self.get_file_list())
                    if not x.startswith('.coverage')]
        rh_files = [x for x in sorted(other_tree.get_file_list())
                    if not x.startswith('.coverage')]
        if lh_files != rh_files:
            return False
        for fname in lh_files:
            if os.path.isfile(fname):
                if self.get_file_hash(fname) != \
                        other_tree.get_file_hash(fname):
                    return False
        return True


class TestFreezerScenario(BaseFreezerCliTest):
    def setUp(self):
        super(TestFreezerScenario, self).setUp()
        self.source_tree = Temp_Tree()
        self.source_tree.add_random_data()
        self.dest_tree = Temp_Tree()

        self.cli.freezer_scheduler(action='start',
                                   flags='-c test_node '
                                         '-f /tmp/freezer_tempest_job_dir/')

    def tearDown(self):
        super(TestFreezerScenario, self).tearDown()
        self.source_tree.cleanup()
        self.dest_tree.cleanup()

        self.cli.freezer_scheduler(action='stop',
                                   flags='-c test_node '
                                         '-f /tmp/freezer_tempest_job_dir/')

    def test_simple_backup(self):
        backup_job = {
            "client_id": "test_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "backup",
                        "mode": "fs",
                        "storage": "local",
                        "backup_name": "backup1",
                        "path_to_backup": self.source_tree.path,
                        "container": "/tmp/freezer_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a test backup"
        }
        restore_job = {
            "client_id": "test_node",
            "job_actions": [
                {
                    "freezer_action": {
                        "action": "restore",
                        "storage": "local",
                        "restore_abs_path": self.dest_tree.path,
                        "backup_name": "backup1",
                        "container": "/tmp/freezer_test/",
                    },
                    "max_retries": 3,
                    "max_retries_interval": 60
                }
            ],
            "description": "a test restore"
        }

        backup_job_id = self.create_job(backup_job)
        self.cli.freezer_client(action='job-start', params=backup_job_id)
        self.wait_for_job_status(backup_job_id)
        self.assertJobColumnEqual(backup_job_id, JOB_TABLE_RESULT_COLUMN,
                                  'success')

        restore_job_id = self.create_job(restore_job)
        self.wait_for_job_status(restore_job_id)
        self.assertJobColumnEqual(restore_job_id, JOB_TABLE_RESULT_COLUMN,
                                  'success')

        self.assertTrue(self.source_tree.is_equal(self.dest_tree))
