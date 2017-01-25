"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
(c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Freezer general utils functions
"""

import threading

from oslo_log import log
from six.moves import queue


LOG = log.getLogger(__name__)


class Wait(Exception):
    pass


class RichQueue(object):
    """
        :type data_queue: Queue.Queue
    """
    def __init__(self, size=2):
        """
        :type size: int
        :return:
        """
        self.data_queue = queue.Queue(maxsize=size)
        # transmission changes in atomic way so no synchronization needed
        self.finish_transmission = False
        self.is_force_stop = False

    def finish(self):
        self.finish_transmission = True

    def force_stop(self):
        self.is_force_stop = True

    def empty(self):
        return self.data_queue.empty()

    def get(self):
        try:
            res = self.data_queue.get(timeout=1)
            self.data_queue.task_done()
            return res
        except queue.Empty:
            raise Wait()

    def check_stop(self):
        if self.is_force_stop:
            raise Exception("Forced stop")

    def put_messages(self, messages):
        for message in messages:
            self.put(message)
        self.finish()

    def has_more(self):
        self.check_stop()
        return not self.finish_transmission or not self.data_queue.empty()

    def put(self, message):
        while True:
            try:
                self.data_queue.put(message, timeout=1)
                break
            except queue.Full:
                self.check_stop()

    def get_messages(self):
        while self.has_more():
            try:
                yield self.get()
            except Wait:
                self.check_stop()


class QueuedThread(threading.Thread):
    def __init__(self, target, rich_queue, exception_queue,
                 args=(), kwargs=None):
        """
            :type args: collections.Iterable
            :type kwargs: dict
            :type target: () -> ()
            :type rich_queue: RichQueue
            """
        self.args = args
        kwargs = kwargs or {}
        self.rich_queue = rich_queue
        self._exception_queue = exception_queue
        kwargs["rich_queue"] = rich_queue
        super(QueuedThread, self).__init__(target=target, args=args,
                                           kwargs=kwargs)

    def run(self):
        try:
            super(QueuedThread, self).run()
        except Exception as e:
            LOG.exception(e)
            self._exception_queue.put_nowait(e)
            self.rich_queue.force_stop()
            # Thread will exit at this point.
            # @todo print the error using traceback.print_exc(file=sys.stdout)
            raise
