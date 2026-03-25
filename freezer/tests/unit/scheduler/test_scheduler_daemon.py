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

import errno
import signal
import unittest
from unittest import mock
from unittest.mock import patch

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

    @mock.patch('freezer.scheduler.daemon.os.kill')
    def test_is_process_running_eperm(self, mock_kill):
        mock_kill.side_effect = OSError(errno.EPERM, "Operation not permitted")
        self.assertTrue(daemon.is_process_running(1234))

    @mock.patch('freezer.scheduler.daemon.os.kill')
    def test_is_process_running_srch(self, mock_kill):
        mock_kill.side_effect = OSError(errno.ESRCH, "No such process")
        self.assertFalse(daemon.is_process_running(1234))

    @mock.patch('freezer.scheduler.daemon.os.kill')
    def test_is_process_running_success(self, mock_kill):
        mock_kill.return_value = None
        self.assertTrue(daemon.is_process_running(1234))

    @mock.patch('freezer.scheduler.daemon.os.path.exists')
    @mock.patch('freezer.scheduler.daemon.os.listdir')
    @mock.patch('freezer.scheduler.daemon.os.fstat')
    def test_get_open_sockets(self, mock_fstat, mock_listdir, mock_exists):
        import stat
        mock_exists.return_value = True
        mock_listdir.return_value = ['3', '4', '5']

        # fd 3 is a socket
        s3 = mock.Mock()
        s3.st_mode = stat.S_IFSOCK | 0o666

        # fd 4 is a regular file
        s4 = mock.Mock()
        s4.st_mode = stat.S_IFREG | 0o666

        # fd 5 is a socket
        s5 = mock.Mock()
        s5.st_mode = stat.S_IFSOCK | 0o666

        mock_fstat.side_effect = [s3, s4, s5]

        res = daemon.get_open_sockets()
        self.assertEqual(res, [3, 5])

    @mock.patch('freezer.scheduler.daemon.PidFile')
    @mock.patch('freezer.scheduler.daemon.DaemonContext')
    @mock.patch('freezer.scheduler.daemon.get_filenos')
    @mock.patch('freezer.scheduler.daemon.get_open_sockets')
    def test_daemon_start_preserves_sockets(
            self, mock_get_sockets, mock_get_filenos,
            mock_DaemonContext, mock_PidFile):

        daemonizable = mock.Mock()
        d = daemon.Daemon(daemonizable=daemonizable)
        d._pid_fname = "/tmp/fake.pid"

        mock_get_filenos.return_value = [10]
        mock_get_sockets.return_value = [20]

        # Mock DaemonContext to act as a proper context manager
        mock_ctx = mock_DaemonContext.return_value
        mock_ctx.__enter__.return_value = mock_ctx

        # Set exit_flag to True immediately to avoid infinite loop
        daemon.Daemon.exit_flag = True

        with mock.patch('freezer.scheduler.daemon.is_process_running',
                        return_value=False):
            d.start()

        # Verify files_preserve includes both filenos and sockets
        args, kwargs = mock_DaemonContext.call_args
        self.assertIn(10, kwargs['files_preserve'])
        self.assertIn(20, kwargs['files_preserve'])

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


class TestGetFilenos(unittest.TestCase):
    def test_get_filenos_with_valid_stream(self):
        mock_handler = mock.Mock(spec=['stream'])
        mock_handler.stream.fileno.return_value = 10
        mock_logger = mock.Mock()
        mock_logger.handlers = [mock_handler]
        mock_logger.parent = None

        result = daemon.get_filenos(mock_logger)
        self.assertCountEqual([10], result)

    def test_get_filenos_no_stream(self):
        # Simulate a handler like OSJournalHandler that lacks a 'stream' attr
        mock_handler = mock.Mock(spec=['level', 'filters', 'lock'])
        mock_logger = mock.Mock()
        mock_logger.handlers = [mock_handler]
        mock_logger.parent = None
        self.assertCountEqual([], daemon.get_filenos(mock_logger))

    def test_get_filenos_stream_no_fileno(self):
        # Simulate a stream object that doesn't have a fileno method
        mock_stream = mock.Mock(spec=[])
        mock_handler = mock.Mock(spec=['stream'])
        mock_handler.stream = mock_stream
        mock_logger = mock.Mock()
        mock_logger.handlers = [mock_handler]
        mock_logger.parent = None
        self.assertCountEqual([], daemon.get_filenos(mock_logger))

    def test_get_filenos_recursive(self):
        handler1 = mock.Mock(spec=['stream'])
        handler1.stream.fileno.return_value = 1
        handler2 = mock.Mock(spec=['stream'])
        handler2.stream.fileno.return_value = 2
        parent = mock.Mock()
        parent.handlers = [handler2]
        parent.parent = None
        child = mock.Mock()
        child.handlers = [handler1]
        child.parent = parent
        self.assertCountEqual([1, 2], daemon.get_filenos(child))

    def test_get_filenos_extended_attributes(self):
        # Test finding filenos through various attributes
        mock_logger = mock.Mock()
        mock_logger.parent = None

        # Handler 1: .stream
        h1 = mock.Mock(spec=['stream'])
        h1.stream.fileno.return_value = 10

        # Handler 2: .socket
        h2 = mock.Mock(spec=['socket'])
        h2.socket.fileno.return_value = 11

        # Handler 3: .sock
        h3 = mock.Mock(spec=['sock'])
        h3.sock.fileno.return_value = 12

        # Handler 4: ._socket
        h4 = mock.Mock(spec=['_socket'])
        h4._socket.fileno.return_value = 13

        mock_logger.handlers = [h1, h2, h3, h4]

        res = daemon.get_filenos(mock_logger)
        self.assertCountEqual(res, [10, 11, 12, 13])
