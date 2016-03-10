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
import unittest

from freezer.utils import bandwidth


class FakeSocket:
    def __init__(self):
        pass

    def recv(self):
        return "abcdef"

    def send(self):
        raise Exception("fake send")


class TestBandwidth(unittest.TestCase):

    def test_throttled_socket_recv(self):
        fake = FakeSocket()
        throttled = bandwidth.ThrottledSocket(100, 100, fake)
        assert throttled.recv() == fake.recv()

    def test_throttled_socket_send(self):
        fake = FakeSocket()
        throttled = bandwidth.ThrottledSocket(100, 100, fake)
        self.assertRaises(Exception, throttled.sendall)

    def test_sleep_duration(self):
        assert bandwidth.ThrottledSocket._sleep_duration(10, 5, 5, 6) == 1.0
        assert bandwidth.ThrottledSocket._sleep_duration(10, 5, 5, 5.5) == 1.5
        assert bandwidth.ThrottledSocket._sleep_duration(10, 5, 5, 6.5) == 0.5
        assert bandwidth.ThrottledSocket._sleep_duration(10, 5, 5, 7) == 0.0

    def test_sleep(self):
        bandwidth.ThrottledSocket._sleep(10, 5, 5, 7)

    def test_monkeypatch(self):
        bandwidth.monkeypatch_bandwidth(100, 100)

    def test_set(self):
        fake = FakeSocket()
        bandwidth.ThrottledSocket(100, 100, fake).__setattr__("test", 12)
        bandwidth.ThrottledSocket(100, 100, fake).__getattr__("test")
