#!/bin/bash

# Copyright 2015 Hewlett-Packard
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


set -x

HOST_ONLY_IP=$(hostname -I|awk '{print $2}')
USER=vagrant

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install git-core -y

git clone https://git.openstack.org/openstack-dev/devstack

sudo cat > devstack/local.conf << E-O-L
[[local|localrc]]
HOST_IP=$HOST_ONLY_IP
DEST=/opt/stack
ADMIN_PASSWORD=admin
DATABASE_PASSWORD=\$ADMIN_PASSWORD
RABBIT_PASSWORD=\$ADMIN_PASSWORD
SERVICE_PASSWORD=\$ADMIN_PASSWORD
SERVICE_TOKEN=a682f596-76f3-11e3-b3b2-e716f9080d50
### Logging ###
LOGFILE=\$DEST/logs/stack.sh.log
LOGDAYS=1
### Services ###
disable_all_services
enable_service key mysql s-proxy s-object s-container s-account
### Swift ###
SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
SWIFT_REPLICAS=1
SWIFT_DATA_DIR=\$DEST/data/swift
GIT_BASE=http://github.com
E-O-L

sudo cat > keystonerc  << E-O-L
unset OS_USERNAME
unset OS_PASSWORD
unset OS_TENANT_NAME
unset OS_AUTH_URL
unset OS_REGION_NAME
unset OS_TENANT_ID

export OS_USERNAME=admin
export OS_PASSWORD=admin
export OS_TENANT_NAME=admin
export OS_AUTH_URL=http://$HOST_ONLY_IP:35357/v2.0
export OS_REGION_NAME=RegionOne
E-O-L

chown ${USER}.${USER} -R *
cd devstack
su ${USER} -c './unstack.sh'
su ${USER} -c './stack.sh'

cd ..
source keystonerc
keystone service-list
sleep 5
keystone service-list
sleep 5
keystone service-list

exit 0;
