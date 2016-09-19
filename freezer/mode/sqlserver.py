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
from freezer.utils import config
from freezer.utils import utils
from freezer.utils import winutils

LOG = log.getLogger(__name__)


class SqlserverMode(mode.Mode):
    """
    Execute a SQL Server DB backup. Currently only backups with shadow
    copy are supported. This mean, as soon as the shadow copy is created
    the db writes will be blocked and a checkpoint will be created, as soon
    as the backup finish the db will be unlocked and the backup will be
    uploaded. A sql_server.conf_file is required for this operation.
    """
    def __init__(self, conf):
        self.released = False
        with open(conf.sql_server_conf, 'r') as sql_conf_file_fd:
            self.sql_server_instance = \
                config.ini_parse(sql_conf_file_fd)["instance"]

    @property
    def name(self):
        return "sqlserver"

    @property
    def version(self):
        return "1.0"

    def stop_sql_server(self):
        """ Stop a SQL Server instance to
        perform the backup of the db files """

        LOG.info('Stopping SQL Server for backup')
        with winutils.DisableFileSystemRedirection():
            cmd = 'net stop "SQL Server ({0})"'\
                .format(self.sql_server_instance)
            (out, err) = utils.create_subprocess(cmd)
            if err != '':
                raise Exception('Error while stopping SQL Server,'
                                ', error {0}'.format(err))

    def start_sql_server(self):
        """ Start the SQL Server instance after the backup is completed """

        with winutils.DisableFileSystemRedirection():
            cmd = 'net start "SQL Server ({0})"'.format(
                self.sql_server_instance)
            (out, err) = utils.create_subprocess(cmd)
            if err != '':
                raise Exception('Error while starting SQL Server'
                                ', error {0}'.format(err))
            LOG.info('SQL Server back to normal')

    def prepare(self):
        self.stop_sql_server()
        self.released = False

    def release(self):
        if not self.released:
            self.released = True
            self.start_sql_server()
