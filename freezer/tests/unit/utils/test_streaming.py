# (c) Copyright 2020 ZTE Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import queue
import unittest

from freezer.utils import streaming


class StreamingTestCase(unittest.TestCase):

    def create_fifo(self, size):
        input_queue = streaming.RichQueue(size)
        read_except_queue = queue.Queue()
        write_except_queue = queue.Queue()

        read_stream = streaming.QueuedThread(self.backup_stream,
                                             input_queue,
                                             read_except_queue)

        write_stream = streaming.QueuedThread(self.write_stream,
                                              input_queue,
                                              write_except_queue)

        read_stream.daemon = True
        write_stream.daemon = True
        read_stream.start()
        write_stream.start()
        read_stream.join()
        write_stream.join()

        return input_queue

    def backup_stream(self, rich_queue):
        rich_queue.put_messages('ancd')

    def write_stream(self, rich_queue):
        for message in rich_queue.get_messages():
            pass

    def test_stream_1(self):
        input_queue = self.create_fifo(1)
        assert input_queue.finish_transmission is True

    def test_stream_2(self):
        input_queue = self.create_fifo(2)
        assert input_queue.finish_transmission is True

    def test_stream_3(self):
        input_queue = self.create_fifo(3)
        assert input_queue.finish_transmission is True

    def test_stream_4(self):
        input_queue = self.create_fifo(4)
        assert input_queue.finish_transmission is True

    def test_stream_5(self):
        input_queue = self.create_fifo(5)
        assert input_queue.finish_transmission is True
