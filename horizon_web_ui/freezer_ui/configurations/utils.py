# Copyright 2014 Hewlett-Packard
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


class Configuration(object):
    def __init__(self, data_dict):
        self.data_dict = data_dict

    @property
    def id(self):
        return self.config_id

    def __getattr__(self, attr):
        """Make data_dict fields available via class interface """
        if attr in self.data_dict:
            return self.data_dict[attr]
        elif attr in self.data_dict['config_file']:
            return self.data_dict['config_file'][attr]
        else:
            return object.__getattribute__(self, attr)


class Client(object):
    """Aggregate clients and metadata """

    def __init__(self, client):
        self.name = client
        self.clients = client
        self.client_id = client
