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
import prettytable
import subprocess
import sys

from oslo_config import cfg
from oslo_log import log

from freezer.common import client_manager
from freezer.common import config as freezer_config
from freezer.engine import manager as engine_manager
from freezer import job
from freezer.storage import local
from freezer.storage import multiple
from freezer.storage import s3
from freezer.storage import ssh
from freezer.storage import swift
from freezer.utils import utils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def freezer_main(backup_args):
    """Freezer main loop for job execution.
    """

    if not backup_args.quiet:
        LOG.info("Begin freezer agent process with args: {0}".format(sys.argv))
        LOG.info('log file at {0}'.format(CONF.get('log_file')))

    if backup_args.max_priority:
        utils.set_max_process_priority()

    backup_args.__dict__['hostname_backup_name'] = "{0}_{1}".format(
        backup_args.hostname, backup_args.backup_name)

    max_segment_size = backup_args.max_segment_size
    if (backup_args.storage ==
            'swift' or
            backup_args.backup_media in ['nova', 'cinder', 'cindernative',
                                         'cinderbrick']):

        backup_args.client_manager = client_manager.get_client_manager(
            backup_args.__dict__)

    if backup_args.storage == 's3':
        if backup_args.__dict__['access_key'] == '' \
                and 'ACCESS_KEY' in os.environ:
            backup_args.__dict__['access_key'] = os.environ.get('ACCESS_KEY')
        if backup_args.__dict__['access_key'] == '':
            raise Exception('No access key found for S3 compatible storage')

        if backup_args.__dict__['secret_key'] == '' \
                and 'SECRET_KEY' in os.environ:
            backup_args.__dict__['secret_key'] = os.environ.get('SECRET_KEY')
        if backup_args.__dict__['secret_key'] == '':
            raise Exception('No secret key found for S3 compatible storage')

        if backup_args.__dict__['endpoint'] == '' \
                and 'ENDPOINT' in os.environ:
            backup_args.__dict__['endpoint'] = os.environ.get('ENDPOINT')
        if backup_args.__dict__['endpoint'] == '':
            raise Exception('No endpoint found for S3 compatible storage')

    if backup_args.storages:
        # pylint: disable=abstract-class-instantiated
        storage = multiple.MultipleStorage(
            [storage_from_dict(x, max_segment_size)
             for x in backup_args.storages])
    else:
        storage = storage_from_dict(backup_args.__dict__, max_segment_size)

    engine_loader = engine_manager.EngineManager()
    backup_args.engine = engine_loader.load_engine(
        compression=backup_args.compression,
        symlinks=backup_args.dereference_symlink,
        exclude=backup_args.exclude,
        storage=storage,
        max_segment_size=backup_args.max_segment_size,
        encrypt_key=backup_args.encrypt_pass_file,
        dry_run=backup_args.dry_run
    )

    if hasattr(backup_args, 'trickle_command'):
        if "tricklecount" in os.environ:
            if int(os.environ.get("tricklecount")) > 1:
                LOG.critical("Trickle seems to be not working,  Switching "
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
                print(line)
        output, error = process.communicate()

        if hasattr(backup_args, 'tmp_file'):
            utils.delete_file(backup_args.tmp_file)

        if process.returncode:
            LOG.warning("Trickle Error: {0}".format(error))
            LOG.info("Switching to work without trickle ...")
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

    start_time = utils.DateTime.now()
    LOG.info('Job execution Started at: {0}'.format(start_time))
    response = freezer_job.execute()
    end_time = utils.DateTime.now()
    LOG.info('Job execution Finished, at: {0}'.format(end_time))
    LOG.info('Job time Elapsed: {0}'.format(end_time - start_time))
    LOG.info('Backup metadata received: {0}'.format(json.dumps(response)))
    if not conf.quiet:
        LOG.info("End freezer agent process successfully")

    if conf.metadata_out and response:
        if conf.metadata_out == '-':
            sys.stdout.write(json.dumps(response))
            sys.stdout.flush()
        else:
            with open(conf.metadata_out, 'w') as outfile:
                outfile.write(json.dumps(response))
    elif response and isinstance(response, dict):
        pp = prettytable.PrettyTable(["Property", "Value"])
        for k, v in response.items():
            k = k.replace("_", " ")
            pp.add_row([k, v])
        sys.stdout.writelines(pp.get_string())
        sys.stdout.write('\n')
        sys.stdout.flush()
    elif response and isinstance(response, list):
        pp = prettytable.PrettyTable()
        pp.field_names = response[0]
        for i in response[1]:
            pp.add_row(i)
        print (pp)
    else:
        return


def fail(exit_code, e, quiet, do_log=True):
    """ Catch the exceptions and write it to log """
    msg = 'Critical Error: {0}\n'.format(e)
    if not quiet:
        sys.stderr.write(msg)
        sys.stderr.flush()
    if do_log:
        LOG.critical(msg)
    return exit_code


def storage_from_dict(backup_args, max_segment_size):
    storage_name = backup_args['storage']
    container = backup_args['container']

    if storage_name == "swift":
        client_manager = backup_args['client_manager']

        storage = swift.SwiftStorage(
            client_manager, container, max_segment_size)
    elif storage_name == "s3":
        storage = s3.S3Storage(
            backup_args['access_key'],
            backup_args['secret_key'],
            backup_args['endpoint'],
            container,
            max_segment_size
        )
    elif storage_name == "local":
        storage = local.LocalStorage(
            storage_path=container,
            max_segment_size=max_segment_size)
    elif storage_name == "ssh":
        storage = ssh.SshStorage(
            container,
            backup_args['ssh_key'], backup_args['ssh_username'],
            backup_args['ssh_host'],
            int(backup_args.get('ssh_port', freezer_config.DEFAULT_SSH_PORT)),
            max_segment_size=max_segment_size)
    else:
        raise Exception("No storage found for name {0}".format(
            backup_args['storage']))

    return storage


def main():
    """freezer-agent binary main execution"""
    backup_args = None
    try:

        freezer_config.config(args=sys.argv[1:])
        freezer_config.setup_logging()
        backup_args = freezer_config.get_backup_args()
        if backup_args.config:
            # reload logging configuration to force oslo use the new log path
            if backup_args.log_config_append:
                CONF.set_override('log_config_append',
                                  backup_args.log_config_append)

            freezer_config.setup_logging()

        if len(sys.argv) < 2:
            CONF.print_help()
            sys.exit(1)
        freezer_main(backup_args)

    except Exception as err:
        quiet = backup_args.quiet if backup_args else False
        LOG.exception(err)
        LOG.critical("End freezer agent process unsuccessfully")
        return fail(1, err, quiet)

if __name__ == '__main__':
    sys.exit(main())
