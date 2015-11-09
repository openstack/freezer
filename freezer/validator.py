# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def validate(conf):
    if conf.no_incremental and (conf.max_level or conf.always_level):
        raise Exception(
            'no-incremental option is not compatible '
            'with backup level options')

    if conf.action == "restore" and not conf.restore_abs_path and \
            not conf.nova_inst_id and not conf.cinder_vol_id and \
            not conf.cindernative_vol_id:
        raise Exception("Please provide restore_abs_path")

    if conf.restore_abs_path and not conf.action == "restore":
        raise Exception('Restore abs path with {0} action'
                        .format(conf.action))

    if conf.storage == "ssh" and \
            not (conf.ssh_key and conf.ssh_username and conf.ssh_host):
        raise Exception("Please provide ssh_key, "
                        "ssh_username and ssh_host")
