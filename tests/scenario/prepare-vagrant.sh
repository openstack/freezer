#!/usr/bin/env bash

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
#


if [ "X$(python -mplatform | grep Ubuntu)" == "X" ]; then
    echo "Only Ubunu support!";
    exit 1;
fi

if [ ! -e /usr/bin/vagrant ]; then
    ### Download Vagrant 1.7.2 ###
    wget https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.deb || exit 1;
    sudo dpkg -i vagrant*.deb || exit 1;
fi
sudo apt-get -y install virtualbox || exit 1;

### VAGRANT LIBVIRT ###
sudo apt-get -y install libxslt-dev libxml2-dev libvirt-dev qemu-kvm || exit 1;
if [ "X$(vagrant plugin list|awk '{print $1}'|grep vagrant-libvirt)" == "X" ]; then
    vagrant plugin install vagrant-libvirt || exit 1;
fi

### VAGRANT MUTATE ###
sudo apt-get -y install qemu-utils || exit 1;
if [ "X$(vagrant plugin list|awk '{print $1}'|grep vagrant-mutate)" == "X" ]; then
    vagrant plugin install vagrant-mutate || exit 1;
fi

### UBUNTU 14.04 - TRUSTY 64BIT ###
if [ "$(vagrant box list|awk '{print $1}'|grep ^trusty64|wc -l)" != "2" ]; then
    vagrant box add --force trusty64 https://vagrantcloud.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box || exit 1;
    vagrant mutate trusty64 libvirt || exit 1;
fi

### CREATE VAGRANT MACHINE ###
#vagrant destroy -f || exit 1;
time vagrant up || exit 1

exit 0;
