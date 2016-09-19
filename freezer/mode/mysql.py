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

from freezer.mode import mode
from freezer.utils import config


class MysqlMode(mode.Mode):
    """
    Execute a MySQL DB backup. currently only backup with lvm snapshots
    are supported. This mean, just before the lvm snap vol is created,
    the db tables will be flushed and locked for read, then the lvm create
    command will be executed and after that, the table will be unlocked and
    the backup will be executed. It is important to have the available in
    backup_args.mysql_conf the file where the database host, name, user,
    password and port are set.
    """

    @property
    def name(self):
        return "mysql"

    @property
    def version(self):
        return "1.0"

    def release(self):
        if not self.released:
            self.released = True
            self.cursor.execute('UNLOCK TABLES')
            self.mysql_db_inst.commit()
            self.cursor.close()
            self.mysql_db_inst.close()

    def prepare(self):
        self.released = False
        self.cursor = self.mysql_db_inst.cursor()
        self.cursor.execute('FLUSH TABLES WITH READ LOCK')
        self.mysql_db_inst.commit()

    def __init__(self, conf):
        try:
            import pymysql as MySQLdb
        except ImportError:
            raise ImportError('Please install PyMySQL module')

        with open(conf.mysql_conf, 'r') as mysql_file_fd:
            parsed_config = config.ini_parse(mysql_file_fd)
        # Initialize the DB object and connect to the db according to
        # the db mysql backup file config
        self.released = False
        try:
            self.mysql_db_inst = MySQLdb.connect(
                host=parsed_config.get("host", False),
                port=int(parsed_config.get("port", 3306)),
                user=parsed_config.get("user", False),
                passwd=parsed_config.get("password", False))
            self.cursor = None
        except Exception as error:
            raise Exception('MySQL: {0}'.format(error))
