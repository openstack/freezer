"""
Copyright 2015 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import logging
import os
import signal
import traceback

from tempfile import gettempdir
from time import sleep


from freezer.lib.pep3143daemon import DaemonContext
from freezer.lib.pep3143daemon import PidFile
from freezer.utils import utils


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
        '/var/log/freezer-scheduler.log',
        '~/.freezer/freezer-scheduler.log']
    for file_name in log_file_paths:
        try:
            return configure_logging(file_name)
        except IOError:
            pass

    raise Exception("Unable to write to log file")


class NoDaemon(object):
    """
    A class which shares the same interface as the Daemon class,
    but is used to execute the scheduler as a foreground process

    """

    instance = None
    exit_flag = False

    def __init__(self, daemonizable):
        # daemonizable has to provide start/stop (and possibly reload) methods
        NoDaemon.instance = self
        self.daemonizable = daemonizable

        # register signal handlers
        for (signal_number, handler) in self.signal_map.items():
            signal.signal(signal_number, handler)

    @property
    def signal_map(self):
        return {
            signal.SIGTERM: NoDaemon.handle_program_exit,
            signal.SIGINT: NoDaemon.handle_program_exit,
            signal.SIGHUP: NoDaemon.handle_reload,
        }

    @staticmethod
    def handle_program_exit(signum, frame):
        logging.info('Got signal {0}. Exiting ...'.format(signum))
        NoDaemon.exit_flag = True
        NoDaemon.instance.daemonizable.stop()

    @staticmethod
    def handle_reload(signum, frame):
        NoDaemon.instance.daemonizable.reload()

    def start(self, log_file=None, dump_stack_trace=False):
        setup_logging(log_file)
        while not NoDaemon.exit_flag:
            try:
                logging.info('Starting in no-daemon mode')
                self.daemonizable.start()
                NoDaemon.exit_flag = True
            except Exception as e:
                if dump_stack_trace:
                    logging.error(traceback.format_exc(e))
                logging.error('Restarting procedure in no-daemon mode '
                              'after Fatal Error: {0}'.format(e))
                sleep(10)
        logging.info('Done exiting')

    def stop(self):
        pass

    def status(self):
        pass


class Daemon(object):
    """
    A class to manage all the daemon-related stuff

    """

    instance = None
    exit_flag = False

    def __init__(self, daemonizable=None, pid_fname=None):
        # daemonizable has to provide start/stop (and possibly reload) methods
        Daemon.instance = self
        self._pid_fname = pid_fname
        self.daemonizable = daemonizable

    @staticmethod
    def handle_program_exit(signum, frame):
        Daemon.exit_flag = True
        Daemon.instance.daemonizable.stop()

    @staticmethod
    def handle_reload(signum, frame):
        Daemon.instance.daemonizable.reload()

    @property
    def signal_map(self):
        return {
            signal.SIGTERM: Daemon.handle_program_exit,
            signal.SIGHUP: Daemon.handle_reload,
        }

    @property
    def pid_fname(self):
        if not self._pid_fname:
            fname = '{0}/freezer_sched_{1}.pid'.format(
                gettempdir(),
                os.path.split(os.path.expanduser('~'))[-1])
            self._pid_fname = os.path.normpath(fname)
        return self._pid_fname

    @property
    def pid(self):
        if os.path.isfile(self.pid_fname):
            with open(self.pid_fname, 'r') as f:
                return int(f.read())
        return None

    def start(self, log_file=None, dump_stack_trace=False):
        pidfile = PidFile(self.pid_fname)
        with DaemonContext(pidfile=pidfile, signal_map=self.signal_map):
            setup_logging(log_file)
            while not Daemon.exit_flag:
                try:
                    logging.info('freezer daemon starting, pid: {0}'.
                                 format(self.pid))
                    self.daemonizable.start()
                    Daemon.exit_flag = True
                except Exception as e:
                    if dump_stack_trace:
                        logging.error(traceback.format_exc(e))
                    logging.error('Restarting daemonized procedure '
                                  'after Fatal Error: {0}'.format(e))
                    sleep(10)
            logging.info('freezer daemon done, pid: {0}'.format(self.pid))

    def stop(self):
        pid = self.pid
        if pid:
            os.kill(self.pid, signal.SIGTERM)
        else:
            print('Not Running')

    def status(self):
        pid = self.pid
        if pid:
            print('Running with pid: {0}'.format(pid))
        else:
            print('Not Running')

    def reload(self):
        pid = self.pid
        if pid:
            os.kill(pid, signal.SIGHUP)
        else:
            print('Not Running')
