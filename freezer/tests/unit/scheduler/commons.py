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

from freezer.scheduler import arguments
from oslo_config import cfg

CONF = cfg.CONF


def set_test_capabilities():
    arguments.configure_capabilities_options()
    CONF.capabilities.supported_actions = ['backup']
    CONF.capabilities.supported_modes = ['cindernative']
    CONF.capabilities.supported_storages = ['swift']
    CONF.capabilities.supported_engines = []


def set_default_capabilities():
    CONF.capabilities.supported_actions = arguments.DEFAULT_SUPPORTED_ACTIONS
    CONF.capabilities.supported_modes = arguments.DEFAULT_SUPPORTED_MODES
    CONF.capabilities.supported_storages = arguments.DEFAULT_SUPPORTED_STORAGES
    CONF.capabilities.supported_engines = arguments.DEFAULT_SUPPORTED_ENGINES
