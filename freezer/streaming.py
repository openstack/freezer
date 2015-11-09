"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

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
import logging
import Queue


class Wait(Exception):
    pass


class StorageManager:

    def __init__(self, input_queue, output_queues):
        """
        :type input_queue: streaming.RichQueue
        :param input_queue:
        :type output_queues: collections.Iterable[streaming.RichQueue]
        :param output_queues:
        :return:
        """
        self.input_queue = input_queue
        self.output_queues = output_queues
        self.broken_output_queues = set()

    def send_message(self, message, finish=False):
        for output_queue in self.output_queues:
            if output_queue not in self.broken_output_queues:
                try:
                    if finish:
                        output_queue.finish()
                    else:
                        output_queue.put(message)
                except Exception as e:
                    logging.exception(e)
                    StorageManager.one_fails_all_fail(
                        self.input_queue, self.output_queues)
                    self.broken_output_queues.add(output_queue)

    def transmit(self):
        for message in self.input_queue.get_messages():
            self.send_message(message)
        self.send_message("", True)

    @staticmethod
    def one_fails_all_fail(input_queue, output_queues):
        input_queue.force_stop()
        for output_queue in output_queues:
            output_queue.force_stop()
        raise Exception("All fail")


class RichQueue:
    """
        :type data_queue: Queue.Queue
    """
    def __init__(self, size=2):
        """
        :type size: int
        :return:
        """
        self.data_queue = Queue.Queue(maxsize=size)
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
        except Queue.Empty:
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
            except Queue.Full:
                self.check_stop()

    def get_messages(self):
        while self.has_more():
            try:
                yield self.get()
            except Wait:
                self.check_stop()


class QueuedThread(threading.Thread):
    def __init__(self, target, rich_queue, args=(), kwargs=None):
        """
            :type args: collections.Iterable
            :type kwargs: dict
            :type target: () -> ()
            :type rich_queue: RichQueue
            """
        self.args = args
        kwargs = kwargs or {}
        self.rich_queue = rich_queue
        kwargs["rich_queue"] = rich_queue
        super(QueuedThread, self).__init__(target=target, args=args,
                                           kwargs=kwargs)

    def run(self):
        try:
            super(QueuedThread, self).run()
        except Exception as e:
            self.rich_queue.force_stop()
            raise e


def stream(read_function, read_function_kwargs,
           write_function, write_function_kwargs, queue_size=10):
    """
    :param queue_size:
    :type queue_size: int
    :return:
    """
    input_queue = RichQueue(queue_size)
    read_stream = QueuedThread(read_function, input_queue,
                               kwargs=read_function_kwargs)
    output_queue = RichQueue(queue_size)
    write_stream = QueuedThread(write_function, output_queue,
                                kwargs=write_function_kwargs)
    read_stream.daemon = True
    write_stream.daemon = True
    read_stream.start()
    write_stream.start()
    manager = StorageManager(input_queue, [output_queue])
    manager.transmit()
    read_stream.join()
    write_stream.join()
