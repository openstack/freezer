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


REMOTE_USER=vagrant
REMOTE_PASS=vagrant
REMOTE_HOST=10.199.199.199

if [ ! -e /usr/bin/sshpass ]; then
    sudo apt-get install sshpass -y || sudo yum install sshpass -y
fi
if [ ! -e /usr/bin/rsync ]; then
    sudo apt-get install rsync -y || sudo yum install rsync -y
fi

ssh-keygen -R ${REMOTE_HOST}
sshpass -p ${REMOTE_PASS} ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} echo
sshpass -p ${REMOTE_PASS} rsync -azvr --exclude '.git/' --exclude '.vagrant' --exclude '.tox' \
    --exclude '*.pyc' ./../../ ${REMOTE_USER}@${REMOTE_HOST}:~/freezer
# Quotes below are important and without them tests will run on the localhost
sshpass -p ${REMOTE_PASS} ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd freezer/tests/scenario/ && sudo ./run-local.py'

exit 0;
