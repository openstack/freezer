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

import abc
import multiprocessing
import six
import time

from oslo_config import cfg
from oslo_log import log

from freezer.utils import streaming
from freezer.utils import utils

CONF = cfg.CONF
logging = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BackupEngine(object):
    """
    The main part of making a backup and making a restore is the mechanism of
    implementing it. For a long time Freezer had only one mechanism of doing it -
    invoking gnutar and it was heavy hard-coded.

    Currently we are going to support many different approaches.
    One of them is rsync. Having many different implementations requires to
    have an abstraction level

    This class is an abstraction over all implementations.

    Workflow:
    1) invoke backup
        1.1) try to download metadata for incremental
        1.2) create a dataflow between backup_stream and storage.write_backup
            Backup_stream is producer of data, for tar backup
            it creates a gnutar subprocess and start to read data from stdout
            Storage write_backup is consumer of data, it creates a thread
            that store data in storage.
            Both streams communicate in non-blocking mode
        1.3) invoke post_backup - now it uploads metadata file
    2) restore backup
        2.1) define all incremental backups
        2.2) for each incremental backup create a dataflow between
            storage.read_backup and restore_stream
            Read_backup is data producer, it reads data chunk by chunk from
            the specified storage and pushes the chunks into a queue.
            Restore stream is a consumer, that is actually does restore (for
            tar it is a thread that creates gnutar subprocess and feeds chunks
            to stdin of this thread.
    """
    def backup_stream(self, backup_path, rich_queue, manifest_path):
        """
        :param rich_queue:
        :type rich_queue: freezer.streaming.RichQueue
        :param manifest_path:
        :return:
        """
        rich_queue.put_messages(self.backup_data(backup_path, manifest_path))

    def backup(self, backup_path, backup, queue_size=2):
        """
        Here we now location of all interesting artifacts like metadata
        Should return stream for storing data.
        :return: stream
        """
        manifest = backup.storage.download_meta_file(backup)
        input_queue = streaming.RichQueue(queue_size)
        read_stream = streaming.QueuedThread(
            self.backup_stream, input_queue,
            kwargs={"backup_path": backup_path, "manifest_path": manifest})
        write_stream = streaming.QueuedThread(
            backup.storage.write_backup, input_queue,
            kwargs={"backup": backup})
        read_stream.daemon = True
        write_stream.daemon = True
        read_stream.start()
        write_stream.start()
        read_stream.join()
        write_stream.join()
        self.post_backup(backup, manifest)

    @abc.abstractmethod
    def post_backup(self, backup, manifest_file):
        """
        Uploading manifest, cleaning temporary files
        :return:
        """
        pass

    def read_blocks(self, backup, write_pipe, read_pipe):
        # Close the read pipe in this child as it is unneeded
        # and download the objects from swift in chunks. The
        # Chunk size is set by RESP_CHUNK_SIZE and sent to che write
        # pipe
        read_pipe.close()
        for block in backup.storage.backup_blocks(backup):
            write_pipe.send_bytes(block)

        # Closing the pipe after checking no data
        # is still available in the pipe.
        while True:
            if not write_pipe.poll():
                write_pipe.close()
                break
            time.sleep(1)

    def restore(self, backup, restore_path, overwrite):
        """
        :type backup: freezer.storage.Backup
        """
        logging.info("Creation restore path: {0}".format(restore_path))
        utils.create_dir_tree(restore_path)
        if not overwrite and not utils.is_empty_dir(restore_path):
            raise Exception(
                "Restore dir is not empty. "
                "Please use --overwrite or provide different path.")
        logging.info("Creation restore path completed")
        for level in range(0, backup.level + 1):
            b = backup.full_backup.increments[level]
            logging.info("Restore backup {0}".format(b))
            read_pipe, write_pipe = multiprocessing.Pipe()
            process_stream = multiprocessing.Process(
                target=self.read_blocks,
                args=(b, write_pipe, read_pipe))
            process_stream.daemon = True
            process_stream.start()
            write_pipe.close()

            # Start the tar pipe consumer process
            tar_stream = multiprocessing.Process(
                target=self.restore_level,
                args=(restore_path, read_pipe, backup))
            tar_stream.daemon = True
            tar_stream.start()
            read_pipe.close()
            write_pipe.close()
            process_stream.join()
            tar_stream.join()

            if tar_stream.exitcode:
                raise Exception('failed to restore file')

        logging.info(
            '[*] Restore execution successfully executed \
             for backup name {0}'.format(backup))

    @abc.abstractmethod
    def restore_level(self, restore_path, read_pipe, backup):
        pass

    @abc.abstractmethod
    def backup_data(self, backup_path, manifest_path):
        """
        :param backup_path:
        :param manifest_path:
        :return:
        """
        pass
