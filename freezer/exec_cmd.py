# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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

import subprocess


def execute(cmd):
    """
    Split a command specified as function arguments into separate sub commands
    executed separately
    """
    cmds = cmd.split('|')
    nb_process = len(cmds)
    index = 1
    process = None
    for sub_cmd in cmds:
        is_last_process = (index == nb_process)
        process = popen_call(sub_cmd.split(' '), process, is_last_process)
        index += 1


def popen_call(sub_cmd, input, is_last_process):
    """
    Execute a command specified as function arguments using the given input
    """
    if not input:
        process = subprocess.Popen(sub_cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=False)
    else:
        process = subprocess.Popen(sub_cmd,
                                   stdout=subprocess.PIPE, stdin=input.stdout,
                                   stderr=subprocess.PIPE, shell=False)
        input.stdout.close()
    if (is_last_process):
        process.communicate()[0]
        rc = process.returncode
        if rc != 0:
            raise Exception('Error: while executing script '
                            '%s return code was %d instead of 0'
                            % (' '.join(sub_cmd), rc))
    return process
