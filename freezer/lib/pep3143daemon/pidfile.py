# flake8: noqa
# The MIT License (MIT)
#
# Copyright (c) 2014 Stephan Schultchen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -*- coding: utf-8 -*-
"""
Simple PidFile Module for a pep3143 daemon implementation.

"""
__author__ = 'schlitzer'


import atexit
import fcntl
import os


class PidFile(object):
    """
    PidFile implementation for PEP 3143 Daemon.

    This Class can also be used with pythons 'with'
    statement.

    :param pidfile:
        filename to be used as pidfile, including path
    :type pidfile: str
    """

    def __init__(self, pidfile):
        """
        Create a new instance
        """
        self._pidfile = pidfile
        self.pidfile = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            self.release()
            return False
        self.release()
        return True

    def acquire(self):
        """Acquire the pidfile.

        Create the pidfile, lock it, write the pid into it
        and register the release with atexit.


        :return: None
        :raise: SystemExit
        """
        try:
            pidfile = open(self._pidfile, "a")
        except IOError as err:
            raise SystemExit(err)
        try:
            fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit('Already running according to ' + self._pidfile)
        pidfile.seek(0)
        pidfile.truncate()
        pidfile.write(str(os.getpid()) + '\n')
        pidfile.flush()
        self.pidfile = pidfile
        atexit.register(self.release)

    def release(self):
        """Release the pidfile.

        Close and delete the Pidfile.


        :return: None
        """
        try:
            self.pidfile.close()
            os.remove(self._pidfile)
        except OSError as err:
            if err.errno != 2:
                raise
