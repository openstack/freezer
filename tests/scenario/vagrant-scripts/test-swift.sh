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


set +x

SERVICE_IP=127.0.0.1

if [ "X$1" != "X" ]; then
    SERVICE_IP=$1
fi

#SW="swift -v -V 2.0 -A http://$SERVICE_IP:5000/v2.0/ --os-username=admin --os-password=admin --os-tenant-name=admin"
SW="swift"

function get_status() {
  if [ $? -eq 0 ]; then
    echo "OK"
  else
    echo "FAIL"
  fi
}

sudo apt-get install python-swiftclient -y 2>&1 > /dev/null
source keystonerc

$SW post TEST 2>&1 > /dev/null
get_status

$SW list TEST 2>&1 > /dev/null
get_status

SOURCE_DIR='/etc/swift /etc/apache2'
$SW upload TEST $SOURCE_DIR 2>&1 > /dev/null
get_status

$SW delete TEST  2>&1 > /dev/null
get_status
