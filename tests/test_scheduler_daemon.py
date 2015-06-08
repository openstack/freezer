# Copyright 2015 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import unittest
from mock import Mock, patch

import signal

from freezer.scheduler import daemon


class TestOpenstackOptions(unittest.TestCase):

    def setUp(self):
        self.daemonizable = Mock()
        self.daemon = daemon.Daemon(daemonizable=self.daemonizable)

    def test_create(self):
        self.assertIsInstance(self.daemon, daemon.Daemon)

    @patch('freezer.scheduler.daemon.logging')
    def test_setup_logging_default(self, mock_logging):
        res = self.daemon.setup_logging(None)
        self.assertEqual(res, '/var/log/freezer-scheduler.log')

    @patch('freezer.scheduler.daemon.create_dir')
    @patch('freezer.scheduler.daemon.logging')
    def test_setup_logging_userdefined(self, mock_logging, mock_createdir):
        res = self.daemon.setup_logging('mylogfile')
        self.assertEqual(res, 'mylogfile')

    def test_handle_program_exit_calls_scheduler_stop(self):
        self.daemon.handle_program_exit(Mock(), Mock())
        self.daemonizable.stop.assert_called_with()

    def test_handle_program_reload_calls_scheduler_reload(self):
        self.daemon.handle_reload(Mock(), Mock())
        self.daemonizable.reload.assert_called_with()

    def test_signal_map_handlers(self):
        signal_map = self.daemon.signal_map
        self.assertEqual(signal_map[signal.SIGTERM], self.daemon.handle_program_exit)
        self.assertEqual(signal_map[signal.SIGHUP], self.daemon.handle_reload)

    @patch('freezer.scheduler.daemon.gettempdir')
    @patch('freezer.scheduler.daemon.os.path.expanduser')
    def test_pid_fname_in_tempdir(self, mock_expanduser, mock_gettempdir):
        mock_expanduser.return_value = '/home/chet'
        mock_gettempdir.return_value = '/tempus_fugit'
        retval = self.daemon.pid_fname
        self.assertEqual(retval, '/tempus_fugit/freezer_sched_chet.pid')
