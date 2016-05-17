"""
Copyright 2015 Hewlett-Packard
(c) Copyright 2016 Hewlett Packard Enterprise Development Company LP

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Freezer main execution function
"""
import json
import os
import subprocess
import sys

from oslo_config import cfg
from oslo_log import log

from freezer.common import config as freezer_config
from freezer.engine.tar import tar_engine
from freezer import job
from freezer.openstack import osclients
from freezer.storage import local
from freezer.storage import multiple
from freezer.storage import ssh
from freezer.storage import swift
from freezer.utils import config
from freezer.utils import utils
from freezer.utils import validator
from freezer.utils import winutils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def freezer_main(backup_args):
    """Freezer main loop for job execution.
    """

    if not backup_args.quiet:
        LOG.info('log file at {0}'.format(CONF.get('log_file')))

    if backup_args.max_priority:
        utils.set_max_process_priority()

    backup_args.__dict__['hostname_backup_name'] = "{0}_{1}".format(
        backup_args.hostname, backup_args.backup_name)

    validator.validate(backup_args)

    work_dir = backup_args.work_dir
    max_segment_size = backup_args.max_segment_size
    if backup_args.storage == 'swift' or (
                backup_args.backup_media in ['nova', 'cinder', 'cindernative']):
        backup_args.client_manager = get_client_manager(backup_args.__dict__)

    if backup_args.storages:
        storage = multiple.MultipleStorage(
            work_dir,
            [storage_from_dict(x, work_dir, max_segment_size)
             for x in backup_args.storages])
    else:
        storage = storage_from_dict(backup_args.__dict__, work_dir,
                                    max_segment_size)

    backup_args.engine = tar_engine.TarBackupEngine(
        backup_args.compression,
        backup_args.dereference_symlink,
        backup_args.exclude,
        storage,
        winutils.is_windows(),
        backup_args.max_segment_size,
        backup_args.encrypt_pass_file,
        backup_args.dry_run)

    if hasattr(backup_args, 'trickle_command'):
        if "tricklecount" in os.environ:
            if int(os.environ.get("tricklecount")) > 1:
                LOG.critical("[*] Trickle seems to be not working,  Switching "
                             "to normal mode ")
                return run_job(backup_args, storage)

        freezer_command = '{0} {1}'.format(backup_args.trickle_command,
                                           ' '.join(sys.argv))
        LOG.debug('Trickle command: {0}'.format(freezer_command))
        process = subprocess.Popen(freezer_command.split(),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   env=os.environ.copy())
        while process.poll() is None:
            line = process.stdout.readline().strip()
            if line != '':
                print (line)
        output, error = process.communicate()

        if hasattr(backup_args, 'tmp_file'):
            utils.delete_file(backup_args.tmp_file)

        if process.returncode:
            LOG.warn("[*] Trickle Error: {0}".format(error))
            LOG.info("[*] Switching to work without trickle ...")
            return run_job(backup_args, storage)

    else:
        return run_job(backup_args, storage)


def run_job(conf, storage):
    freezer_job = {
        'backup': job.BackupJob,
        'restore': job.RestoreJob,
        'info': job.InfoJob,
        'admin': job.AdminJob,
        'exec': job.ExecJob}[conf.action](conf, storage)
    response = freezer_job.execute()

    if conf.metadata_out and response:
        if conf.metadata_out == '-':
            sys.stdout.write(json.dumps(response))
        else:
            with open(conf.metadata_out, 'w') as outfile:
                outfile.write(json.dumps(response))


def fail(exit_code, e, quiet, do_log=True):
    """ Catch the exceptions and write it to log """
    msg = '[*] Critical Error: {0}\n'.format(e)
    if not quiet:
        sys.stderr.write(msg)
    if do_log:
        LOG.critical(msg)
    return exit_code


def parse_osrc(file_name):
    with open(file_name, 'r') as osrc_file:
        return config.osrc_parse(osrc_file.read())


def get_client_manager(backup_args):
    if "osrc" in backup_args:
        options = osclients.OpenstackOpts.create_from_dict(
            parse_osrc(backup_args['osrc']))
    else:
        options = osclients.OpenstackOpts.create_from_env().get_opts_dicts()

    client_manager = osclients.OSClientManager(
        auth_url=options.pop('auth_url', None),
        auth_method=options.pop('auth_method', 'password'),
        dry_run=backup_args.get('dry_run', None),
        **options
    )
    return client_manager


def storage_from_dict(backup_args, work_dir, max_segment_size):
    storage_name = backup_args['storage']
    container = backup_args['container']
    if storage_name == "swift":
        client_manager = backup_args['client_manager']

        storage = swift.SwiftStorage(
            client_manager, container, work_dir, max_segment_size)
    elif storage_name == "local":
        storage = local.LocalStorage(container, work_dir)
    elif storage_name == "ssh":
        storage = ssh.SshStorage(
            container, work_dir,
            backup_args['ssh_key'], backup_args['ssh_username'],
            backup_args['ssh_host'],
            int(backup_args.get('ssh_port', freezer_config.DEFAULT_SSH_PORT)))
    else:
        raise Exception("Not storage found for name {0}".format(
            backup_args['storage']))
    return storage


def main():
    """freezer-agent binary main execution"""
    backup_args = None
    try:
        freezer_config.config()
        freezer_config.setup_logging()
        backup_args = freezer_config.get_backup_args()
        if len(sys.argv) < 2:
            CONF.print_help()
            sys.exit(1)
        freezer_main(backup_args)
    except Exception as err:
        quiet = backup_args.quiet if backup_args else False
        return fail(1, err, quiet)

if __name__ == '__main__':
    sys.exit(main())
