# Copyright 2015 Hewlett-Packard
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

import logging
import os

import win32serviceutil

from freezer.utils import utils
from freezer.utils import winutils


def setup_logging(log_file):

    class NoLogFilter(logging.Filter):
        def filter(self, record):
            return False

    def configure_logging(file_name):
        expanded_file_name = os.path.expanduser(file_name)
        expanded_dir_name = os.path.dirname(expanded_file_name)
        utils.create_dir(expanded_dir_name, do_log=False)
        logging.basicConfig(
            filename=expanded_file_name,
            level=logging.INFO,
            format=('%(asctime)s %(name)s %(levelname)s %(message)s'))
        # filter out some annoying messages
        # not the best position for this code
        log_filter = NoLogFilter()
        logging.getLogger("apscheduler.scheduler").\
            addFilter(log_filter)
        logging.getLogger("apscheduler.executors.default").\
            addFilter(log_filter)
        logging.getLogger("requests.packages.urllib3.connectionpool").\
            addFilter(log_filter)
        return expanded_file_name

    log_file_paths = [log_file] if log_file else [
        r'C:\.freezer\freezer-scheduler.log']
    for file_name in log_file_paths:
        try:
            return configure_logging(file_name)
        except IOError:
            pass

    raise Exception("Unable to write to log file")


class Daemon(object):
    """Daemon interface to start a windows service with a freezer-scheduler
    instance
    """
    def __init__(self, daemonizable=None, interval=None, job_path=None,
                 insecure=False, concurrent_jobs=1):
        self.service_name = 'FreezerService'
        self.home = r'C:\.freezer'
        # this is only need it in order to have the same interface as in linux
        self.daemonizable = daemonizable
        self.interval = interval or 60
        self.job_path = job_path or r'C:\.freezer\scheduler\conf.d'
        self.insecure = insecure
        self.concurrent_jobs = concurrent_jobs

    @utils.shield
    def start(self, log_file=None):
        """Initialize freezer-scheduler instance inside a windows service
        """
        setup_logging(log_file)

        utils.create_dir(self.home)

        if self.insecure:
            os.environ['SERVICE_INSECURE'] = 'True'

        # send arguments info to the windows service
        os.environ['SERVICE_JOB_PATH'] = self.job_path
        os.environ['SERVICE_INTERVAL'] = str(self.interval)
        os.environ['SERVICE_CONCURRENT_JOBS'] = str(self.concurrent_jobs)

        winutils.save_environment(self.home)

        print('Freezer Service is starting')
        win32serviceutil.StartService(self.service_name)

    @utils.shield
    def reload(self):
        """Reload the windows service
        """
        win32serviceutil.RestartService(self.service_name)

    @utils.shield
    def stop(self):
        """Stop the windows service by using sc queryex command, if we use
        win32serviceutil.StoptService(self.service_name) it never gets stopped
        because freezer_scheduler.start() blocks the windows service and
        prevents any new signal to reach the service.
        """
        query = 'sc queryex {0}'.format(self.service_name)
        out = utils.create_subprocess(query)[0]
        pid = None
        for line in out.split('\n'):
            if 'PID' in line:
                pid = line.split(':')[1].strip()

        command = 'taskkill /f /pid {0}'.format(pid)
        utils.create_subprocess(command)
        print('Freezer Service has stopped')

    @utils.shield
    def status(self):
        """Return running status of Freezer Service
        by querying win32serviceutil.QueryServiceStatus()
        possible running status:
            1 == stop
            4 == running
        """
        if win32serviceutil.QueryServiceStatus(self.service_name)[1] == 4:
            print("{0} is running normally".format(self.service_name))
        else:
            print("{0} is *NOT* running".format(self.service_name))


class NoDaemon(object):
    """A class that share the same interface as the Daemon class but doesn't
    initialize a windows service to execute the scheduler, it runs in the
    foreground
    """
    def __init__(self, daemonizable=None):
        # this is only need it in order to have the same interface as in linux
        self.daemonizable = daemonizable

    @utils.shield
    def stop(self):
        self.daemonizable.stop()

    def status(self):
        """Need it to have the same interface as Daemon
        """
        pass

    def reload(self):
        """Need it to have the same interface as Daemon
        """
        pass

    @utils.shield
    def start(self, log_file=None):
        self.daemonizable.start()
