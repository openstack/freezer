
# Copyright 2011-2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import socket

from cinderclient import exceptions
from oslo_concurrency import processutils


def get_my_ip():
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return None


def get_root_helper():
    # NOTE (e0ne): We don't use rootwrap now
    return 'sudo'


def require_root(f):
    def wrapper(*args, **kwargs):
        if os.getuid() != 0:
            raise exceptions.CommandError(
                "This command requires root permissions.")
        return f(*args, **kwargs)
    return wrapper


def safe_execute(cmd):
    try:
        processutils.execute(*cmd, root_helper=get_root_helper(),
                             run_as_root=True)
    except processutils.ProcessExecutionError as e:
        print('Command "{0}" execution returned {1} exit code:'.format(
              e.cmd, e.exit_code))
        print('Stderr: {0}'.format(e.stderr))
        print('Stdout: {0}'.format(e.stdout))
