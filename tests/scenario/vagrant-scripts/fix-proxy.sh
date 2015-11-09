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

HOST_IPS=$(hostname -I)
HOST_IPS=$(echo $HOST_IPS)
HOST_IPS=$(echo $HOST_IPS|sed 's/ /,/')

if [ "$1" == "P-R-O-X-Y" ]; then
    exit 0;
fi

# Proxy goes here
PROXY="$1"

sudo cat >> /etc/environment << E-O-L
export http_proxy=$PROXY
export https_proxy=$PROXY
export HTTP_PROXY=$PROXY
export HTTPS_PROXY=$PROXY
export no_proxy=127.0.0.1,localhost,$HOST_IPS
export NO_PROXY=127.0.0.1,localhost,$HOST_IPS
E-O-L

sudo cat > /etc/apt/apt.conf.d/01proxies << E-O-L
Acquire::http::proxy "$PROXY";
Acquire::https::proxy "$PROXY";
E-O-L

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install git-core -y

git config --global http.proxy $PROXY
git config --global https.proxy $PROXY

exit 0;
