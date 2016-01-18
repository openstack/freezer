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

# check for service enabled
if is_service_enabled freezer; then
    if [[ "$1" == "source" || "`type -t install_freezer`" != 'function' ]]; then
        # Initial source
        source $FREEZER_DIR/devstack/lib/freezer
    fi

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Freezer"
        install_freezer
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Freezer"
        configure_freezer_scheduler
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Freezer Scheduler"
        init_freezer_scheduler
        start_freezer_scheduler
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_freezer_scheduler
    fi
fi
