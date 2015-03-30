#!/bin/bash
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
  dd if=/dev/zero of=${IMG_DIR}/freezer-test-lvm${1}.img bs=20 count=1048576
  sudo losetup /dev/loop${1} ${IMG_DIR}/freezer-test-lvm${1}.img
  sudo apt-get install lvm2 -y || yum install lvm2 -y
  sudo pvcreate /dev/loop${1}
  sudo vgcreate freezer-test${1}-volgroup /dev/loop${1}
  sudo lvcreate -L 10M --name freezer-test${1}-vol freezer-test${1}-volgroup
  LVM_VOL=/dev/freezer-test${1}-volgroup/freezer-test${1}-vol
  sudo mkfs.ext4 ${LVM_VOL}
  sudo mkdir -p ${MOUNT_DIR}
  sudo mount ${LVM_VOL} ${MOUNT_DIR}
  df -Th
}

### MAIN ###

# >>> Uncomment if you get stuck <<<
# delete_test_lvm ${1};
# exit 0;

if [ "X$(sudo losetup -a|grep loop${1})" == "X" ]; then
    delete_test_lvm ${1};
    create_test_lvm ${1};
fi

exit 0;
