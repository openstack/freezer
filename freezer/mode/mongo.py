# (c) Copyright 2015,2016 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log

from freezer.mode import mode

LOG = log.getLogger(__name__)


class MongoMode(mode.Mode):
    """
    Execute the necessary tasks for file system backup mode
    """

    @property
    def name(self):
        return "mongo"

    @property
    def version(self):
        return "1.0"

    def release(self):
        pass

    def prepare(self):
        pass

    def __init__(self, conf):
        try:
            import pymongo
        except ImportError:
            raise ImportError('please install pymongo module')

        LOG.info('MongoDB backup is being executed...')
        LOG.info('Checking is the localhost is Master/Primary...')
        # todo unhardcode this
        mongodb_port = '27017'
        local_hostname = conf.hostname
        db_host_port = '{0}:{1}'.format(local_hostname, mongodb_port)
        mongo_client = pymongo.MongoClient(db_host_port)
        master_dict = dict(mongo_client.admin.command("isMaster"))
        if master_dict['me'] != master_dict['primary']:
            raise Exception('localhost {0} is not Master/Primary,\
                exiting...'.format(local_hostname))
