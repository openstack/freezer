"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

Freezer main execution function
"""
import os
import subprocess
import logging
import sys
import json

from freezer.bandwidth import monkeypatch_socket_bandwidth
from freezer import job
from freezer.osclients import ClientManager
from freezer import swift
from freezer import local
from freezer import ssh
from freezer import utils
from freezer.engine import tar_engine
from freezer import winutils

# Initialize backup options
from freezer.validator import Validator


def freezer_main(backup_args, arg_parse):
    """Freezer main loop for job execution.
    """

    def configure_log_file_using_defaults():
        """ Configure log file for freezer """

        dry_run_message = ''
        if backup_args.dry_run:
            dry_run_message = '[DRY_RUN] '

        def configure_logging(file_name):
            expanded_file_name = os.path.expanduser(file_name)
            expanded_dir_name = os.path.dirname(expanded_file_name)
            utils.create_dir(expanded_dir_name, do_log=False)
            logging.basicConfig(
                filename=expanded_file_name,
                level=logging.INFO,
                format=('%(asctime)s %(name)s %(levelname)s {0}%(message)s'.
                        format(dry_run_message)))
            return expanded_file_name

        if backup_args.log_file:
            return configure_logging(backup_args.log_file)

        for file_name in ['/var/log/freezer.log', '~/.freezer/freezer.log']:
            try:
                return configure_logging(file_name)
            except IOError:
                pass

        raise Exception("Unable to write to log file")

    def set_max_process_priority():
        """ Set freezer in max priority on the os """
        # children processes inherit niceness from father
        try:
            logging.warning(
                '[*] Setting freezer execution with high CPU and I/O priority')
            PID = os.getpid()
            # Set cpu priority
            os.nice(-19)
            # Set I/O Priority to Real Time class with level 0
            subprocess.call([
                u'{0}'.format(backup_args.ionice),
                u'-c', u'1', u'-n', u'0', u'-t',
                u'-p', u'{0}'.format(PID)
            ])
        except Exception as priority_error:
            logging.warning('[*] Priority: {0}'.format(priority_error))

    if backup_args.version:
        print "freezer version {0}".format(backup_args.__version__)
        sys.exit(1)

    if len(sys.argv) < 2:
        arg_parse.print_help()
        sys.exit(1)

    try:
        log_file_name = configure_log_file_using_defaults()
    except Exception as err:
        fail(1, err, quiet=backup_args.quiet, do_log=False)

    if not backup_args.quiet:
        logging.info('log file at {0}'.format(log_file_name))

    if backup_args.max_priority:
        set_max_process_priority()

    monkeypatch_socket_bandwidth(backup_args)

    backup_args.__dict__['hostname_backup_name'] = "{0}_{1}".format(
        backup_args.hostname, backup_args.backup_name)

    Validator.validate(backup_args)

    if backup_args.storage == "swift":
        options = utils.OpenstackOptions.create_from_env()
        Validator.validate_env(options)
        identity_api_version = (backup_args.os_identity_api_version or
                                options.identity_api_version)
        client_manager = ClientManager(
            options=options,
            insecure=backup_args.insecure,
            swift_auth_version=identity_api_version,
            dry_run=backup_args.dry_run)

        storage = swift.SwiftStorage(
            client_manager, backup_args.container, backup_args.work_dir,
            backup_args.max_segment_size)
        backup_args.__dict__['client_manager'] = client_manager
    elif backup_args.storage == "local":
        storage = local.LocalStorage(backup_args.container,
                                     backup_args.work_dir)
    elif backup_args.storage == "ssh":
        storage = ssh.SshStorage(
            backup_args.container, backup_args.work_dir, backup_args.ssh_key,
            backup_args.ssh_username, backup_args.ssh_host,
            backup_args.ssh_port)
    else:
        raise Exception("Not storage found for name " + backup_args.storage)

    backup_args.__dict__['storage'] = storage
    backup_args.__dict__['engine'] = tar_engine.TarBackupEngine(
        backup_args.tar_path,
        backup_args.compression,
        backup_args.dereference_symlink,
        backup_args.exclude,
        storage,
        winutils.is_windows(),
        backup_args.openssl_path,
        backup_args.encrypt_pass_file,
        backup_args.dry_run)

    freezer_job = job.create_job(backup_args)
    freezer_job.execute()

    if backup_args.metadata_out == '-':
        metadata = freezer_job.get_metadata()
        if metadata:
            sys.stdout.write(json.dumps(metadata))


def fail(exit_code, e, quiet, do_log=True):
    """ Catch the exceptions and write it to log """
    msg = '[*] Critical Error: {0}\n'.format(e)
    if not quiet:
        sys.stderr.write(msg)
    if do_log:
        logging.critical(msg)
    sys.exit(exit_code)
