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

import os
import signal
import traceback

from oslo_log import log
from tempfile import gettempdir
from time import sleep


from freezer.lib.pep3143daemon import DaemonContext
from freezer.lib.pep3143daemon import PidFile


LOG = log.getLogger(__name__)


def get_filenos(logger):
    """
    Get a list of file no from logger
    """
    filenos = []
    for handler in logger.handlers:
        filenos.append(handler.stream.fileno())
    if logger.parent:
        filenos += get_filenos(logger.parent)
    return filenos


def is_process_running(pid):
    """
    Checks whether the process is running.

    :param pid: process pid to check
    :return: true if the process is running
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


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
        LOG.info('Got signal {0}. Exiting ...'.format(signum))
        NoDaemon.exit_flag = True
        NoDaemon.instance.daemonizable.stop()

    @staticmethod
    def handle_reload(signum, frame):
        NoDaemon.instance.daemonizable.reload()

    def start(self, dump_stack_trace=False):
        while not NoDaemon.exit_flag:
            try:
                LOG.info('Starting in no-daemon mode')
                self.daemonizable.start()
                NoDaemon.exit_flag = True
            except Exception as e:
                if dump_stack_trace:
                    LOG.error(traceback.format_exc(e))
                LOG.error('Restarting procedure in no-daemon mode '
                          'after Fatal Error: {0}'.format(e))
                sleep(10)
        LOG.info('Done exiting')

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

    def start(self, dump_stack_trace=False):
        if os.path.exists(self.pid_fname) and \
                is_process_running(self.pid):
            print('freezer daemon is already running, '
                  'pid: {0}'.format(self.pid))
            return
        pidfile = PidFile(self.pid_fname)
        files_preserve = get_filenos(LOG.logger)
        with DaemonContext(pidfile=pidfile, signal_map=self.signal_map,
                           files_preserve=files_preserve):
            while not Daemon.exit_flag:
                try:
                    LOG.info('freezer daemon starting, pid: {0}'.
                             format(self.pid))
                    self.daemonizable.start()
                    Daemon.exit_flag = True
                except Exception as e:
                    if dump_stack_trace:
                        LOG.error(traceback.format_exc(e))
                    LOG.error('Restarting daemonized procedure '
                              'after Fatal Error: {0}'.format(e))
                    sleep(10)
            LOG.info('freezer daemon done, pid: {0}'.format(self.pid))

    def stop(self):
        pid = self.pid
        if pid:
            os.kill(self.pid, signal.SIGTERM)
        else:
            print('Not Running')

    def restart(self):
        pid = self.pid
        if not pid:
            self.start()
        else:
            self.stop()
            sleep(5)
            self.start()

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
