#!/bin/bash
# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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

# set -ex

echo "Start Gate Hook"
# Link the log file so it will be collected by the CI system
if [ -n "$BASE" ] && [ -d "$BASE/logs" ]; then
  sudo ln -sf /home/tempest/.freezer/freezer.log $BASE/logs/freezer.log
  sudo ln -sf $BASE/logs/freezer-scheduler.log $BASE/logs/freezersch.log
fi



#export DEVSTACK_LOCAL_CONFIG="enable_plugin freezer https://git.openstack.org/openstack/freezer"
# export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin freezer-api https://git.openstack.org/openstack/freezer-api"
# Swift is needed for some of the integration tests
export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_service s-proxy s-object s-container s-account"

export DEVSTACK_GATE_TEMPEST_REGEX="freezer_tempest_plugin"

# $BASE/new/devstack-gate/devstack-vm-gate.sh

echo "End Gate Hook"
