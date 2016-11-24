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

import signal
import unittest

import mock
from mock import patch

from freezer.scheduler import daemon


class TestNoDaemon(unittest.TestCase):
    @patch('freezer.scheduler.daemon.signal')
    def setUp(self, mock_signal):
        self.daemonizable = mock.Mock()
        self.daemon = daemon.NoDaemon(daemonizable=self.daemonizable)

    def test_create(self):
        self.assertIsInstance(self.daemon, daemon.NoDaemon)

    def test_exit_handler(self):
        daemon.NoDaemon.exit_flag = False
        self.daemon.handle_program_exit(33, None)
        self.assertEqual(daemon.NoDaemon.exit_flag, True)
        self.assertTrue(self.daemonizable.stop.called)

    def test_reload_handler(self):
        daemon.NoDaemon.exit_flag = False
        self.daemon.handle_reload(33, None)
        self.assertEqual(daemon.NoDaemon.exit_flag, False)
        self.assertTrue(self.daemonizable.reload.called)

    def test_start_exit_ok(self):
        daemon.NoDaemon.exit_flag = False
        res = self.daemon.start(dump_stack_trace=False)
        self.assertIsNone(res)
        self.assertEqual(daemon.NoDaemon.exit_flag, True)
        self.assertTrue(self.daemonizable.start.called)
    #
    # @patch('freezer.scheduler.daemon.logging')
    # def test_start_restarts_daemonizable_on_Exception(self, mock_logging):
    #     daemon.NoDaemon.exit_flag = False
    #     self.daemonizable.start.side_effect = [Exception('test'),
    #                                            lambda: DEFAULT]
    #
    #     res = self.daemon.start(log_file=None, dump_stack_trace=True)
    #
    #     self.assertIsNone(res)
    #     self.assertEqual(daemon.NoDaemon.exit_flag, True)
    #     self.assertEqual(self.daemonizable.start.call_count, 2)
    #     self.assertTrue(mock_logging.error.called)

    def test_has_stop_method(self):
        res = self.daemon.stop()
        self.assertIsNone(res)

    def test_has_status_method(self):
        res = self.daemon.status()
        self.assertIsNone(res)


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.daemonizable = mock.Mock()
        self.daemon = daemon.Daemon(daemonizable=self.daemonizable)

    def test_create(self):
        self.assertIsInstance(self.daemon, daemon.Daemon)

    def test_handle_program_exit_calls_scheduler_stop(self):
        self.daemon.handle_program_exit(mock.Mock(), mock.Mock())
        self.daemonizable.stop.assert_called_with()

    def test_handle_program_reload_calls_scheduler_reload(self):
        self.daemon.handle_reload(mock.Mock(), mock.Mock())
        self.daemonizable.reload.assert_called_with()

    def test_signal_map_handlers(self):
        signal_map = self.daemon.signal_map
        self.assertEqual(self.daemon.handle_program_exit,
                         signal_map[signal.SIGTERM])
        self.assertEqual(self.daemon.handle_reload, signal_map[signal.SIGHUP])

    @patch('freezer.scheduler.daemon.gettempdir')
    @patch('freezer.scheduler.daemon.os.path.expanduser')
    def test_pid_fname_in_tempdir(self, mock_expanduser, mock_gettempdir):
        mock_expanduser.return_value = '/home/chet'
        mock_gettempdir.return_value = '/tempus_fugit'
        retval = self.daemon.pid_fname
        self.assertEqual('/tempus_fugit/freezer_sched_chet.pid', retval)

    @patch('freezer.scheduler.daemon.os.path.isfile')
    def test_pid_not_exists(self, mock_isfile):
        mock_isfile.return_value = False
        res = self.daemon.pid
        self.assertIsNone(res)

    # @patch('freezer.scheduler.daemon.os.path.isfile')
    # def test_pid_exists(self, mock_isfile):
    #     mock_isfile.return_value = True
    #     pid_file_text = "125"
    #     mocked_open_function = mock_open(read_data=pid_file_text)
    #
    #     with patch("__builtin__.open", mocked_open_function):
    #         res = self.daemon.pid
    #
    #     self.assertEqual(res, 125)

    @patch('freezer.scheduler.daemon.PidFile')
    @patch('freezer.scheduler.daemon.DaemonContext')
    def test_start(self, mock_DaemonContext, mock_PidFile):
        daemon.Daemon.exit_flag = False
        res = self.daemon.start()
        self.assertIsNone(res)
        self.assertEqual(daemon.Daemon.exit_flag, True)
        self.assertTrue(self.daemonizable.start.called)

    # @patch('freezer.scheduler.daemon.logging')
    # @patch('freezer.scheduler.daemon.PidFile')
    # @patch('freezer.scheduler.daemon.DaemonContext')
    # def test_start_restarts_daemonizable_on_Exception(
    #         self, mock_DaemonContext, mock_PidFile, mock_logging):
    #     daemon.Daemon.exit_flag = False
    #     self.daemonizable.start.side_effect = [Exception('test'),
    #                                            lambda: DEFAULT]
    #
    #     res = self.daemon.start(log_file=None, dump_stack_trace=True)
    #
    #     self.assertIsNone(res)
    #     self.assertEqual(daemon.Daemon.exit_flag, True)
    #     self.assertEqual(self.daemonizable.start.call_count, 2)
    #     self.assertTrue(mock_logging.error.called)
    #
    # @patch('freezer.scheduler.daemon.os')
    # def test_stop_not_existing(self, mock_os):
    #     self.daemon.pid = None
    #     self.daemon.stop()
    #     self.assertFalse(mock_os.kill.called)
    #
    # @patch('freezer.scheduler.daemon.os')
    # def test_stop_existing(self, mock_os):
    #     self.daemon.pid = 33
    #     self.daemon.stop()
    #     mock_os.kill.assert_called_once_with(33, signal.SIGTERM)
    #
    # @patch('freezer.scheduler.daemon.os')
    # def test_reload_not_existing(self, mock_os):
    #     self.daemon.pid = None
    #     self.daemon.reload()
    #     self.assertFalse(mock_os.kill.called)
    #
    # @patch('freezer.scheduler.daemon.os')
    # def test_reload_existing(self, mock_os):
    #     self.daemon.pid = 33
    #     self.daemon.reload()
    #     mock_os.kill.assert_called_once_with(33, signal.SIGHUP)
    #
    # def test_status_not_existing(self):
    #     self.daemon.pid = None
    #     res = self.daemon.status()
    #     self.assertIsNone(res)
    #
    # def test_status_existing(self):
    #     self.daemon.pid = 33
    #     res = self.daemon.status()
    #     self.assertIsNone(res)
