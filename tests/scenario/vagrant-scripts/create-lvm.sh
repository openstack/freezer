#!/bin/bash

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

set -x
set -e

if [ "X$EUID" != "X0" ]; then
    echo "Please run as root";
    exit 1;
fi

if [ -z "${1##*[!0-9]*}" ]; then
  echo "Please provide /dev/loopX number"
  exit 1;
fi

MOUNT_DIR='/mnt/freezer-test-lvm'
IMG_DIR='/tmp'
IMG_FILE=''
# Sizes in MB
DISK_SIZE=2048
LVM_SIZE=1024

function delete_test_lvm {
  cd ~
  # This should be empty => sudo dmsetup table
  sudo umount -vd ${MOUNT_DIR} || test 0
  sudo rm ${MOUNT_DIR} -rf
  sudo fuser -k /dev/loop${1} || test 0
  sudo dmsetup remove -f freezer--test${1}--volgroup-freezer--test${1}--vol || test 0
  sudo losetup -d /dev/loop${1} || test 0
}

function create_test_lvm {
  IMG_FILE=${IMG_DIR}/freezer-test-lvm${1}.img
  dd if=/dev/zero of=${IMG_FILE} bs=${DISK_SIZE} count=1048576
  sudo losetup /dev/loop${1} ${IMG_FILE}
  sudo apt-get install lvm2 -y || yum install lvm2 -y
  sudo pvcreate /dev/loop${1}
  sudo vgcreate freezer-test${1}-volgroup /dev/loop${1}
  sudo lvcreate -L ${LVM_SIZE}M --name freezer-test${1}-vol freezer-test${1}-volgroup
  LVM_VOL=/dev/freezer-test${1}-volgroup/freezer-test${1}-vol
  sudo mkfs.ext4 ${LVM_VOL}
  sudo mkdir -p ${MOUNT_DIR}
  sudo mount ${LVM_VOL} ${MOUNT_DIR}
  df -Th
}

### MAIN ###

# If LVM image file id older than 7 days recreate
if [ "X$(find ${IMG_FILE} -mtime +7 -print)" != "X" ]; then
    delete_test_lvm ${1};
fi

if [ "X$(sudo losetup -a|grep loop${1})" == "X" ]; then
    create_test_lvm ${1};
fi

exit 0;
