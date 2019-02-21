"""
(c) Copyright 2018 ZTE Corporation.

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

import ftplib
import os
import shutil
import socket
import tempfile

from freezer.storage import fslike
from freezer.utils import utils
from oslo_log import log
from oslo_serialization import jsonutils as json

CHUNK_SIZE = 32768
LOG = log.getLogger(__name__)


class BaseFtpStorage(fslike.FsLikeStorage):
    """
    :type ftp: ftplib
    """
    _type = 'ftpbase'

    def __init__(self, storage_path, remote_pwd,
                 remote_username, remote_ip, port, max_segment_size):
        """
            :param storage_path: directory of storage
            :type storage_path: str
            :return:
            """
        self.remote_username = remote_username
        self.remote_pwd = remote_pwd
        self.remote_ip = remote_ip
        self.port = port
        self.ftp = None
        self._validate()
        self.init()
        super(BaseFtpStorage, self).__init__(
            storage_path=storage_path,
            max_segment_size=max_segment_size)

    def _validate(self):
        """
        Validates if all parameters required to ssh are available.
        :return: True or raises ValueError
        """
        if not self.remote_ip:
            raise ValueError('Please provide --ftp-host value.')
        elif not self.remote_username:
            raise ValueError('Please provide --ftp-username value.')
        elif not self.remote_pwd:
            raise ValueError('Please provide remote password.'
                             '--ftp-password argument.')
        return True

    def init(self):
        pass

    def _create_tempdir(self):
        try:
            tmpdir = tempfile.mkdtemp()
        except Exception:
            LOG.error("Unable to create a tmp directory")
            raise
        return tmpdir

    def rmtree(self, path):
        LOG.info("ftp rmtree path=%s" % path)
        files = []
        self.ftp.dir(path, files.append)
        LOG.info('rm files=%s' % files)
        for f in files:
            attr = f.split()[0]
            file_name = f.split()[-1]
            filepath = utils.path_join(path, file_name)
            if attr.startswith('d'):
                self.rmtree(filepath)
            else:
                self.ftp.delete(filepath)
        self.ftp.rmd(path)

    def create_dirs(self, path):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        LOG.info("ftp create_dirs path=%s" % path)
        if path == '/':
            # absolute path so change directory to root
            self.ftp.cwd('/')
            return
        if path == '':
            # top-level relative directory must exist
            return
        try:
            self.ftp.cwd(path)  # sub-directory exists
        except ftplib.all_errors as e:
            LOG.info("ftp create dirs failed %s" % e)
            dirname, basename = os.path.split(path.rstrip('/'))
            LOG.info("ftp create_dirs dirname=%s basename=%s"
                     % (dirname, basename))
            self.create_dirs(dirname)  # make parent directories
            self.ftp.mkd(basename)  # sub-directory missing, so created it
            self.ftp.cwd(basename)
            return True

    def write_backup(self, rich_queue, backup):
        """
        Stores backup in storage
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        try:
            tmpdir = tempfile.mkdtemp()
        except Exception:
            LOG.error("Unable to create a tmp directory")
            raise

        try:
            data_meta = utils.path_join(tmpdir, "data_meta")
            LOG.info("ftp write data_meta %s" % data_meta)
            backup = backup.copy(storage=self)
            path = backup.data_path
            self.create_dirs(path.rsplit('/', 1)[0])

            with open(data_meta, mode='wb') as b_file:
                for message in rich_queue.get_messages():
                    b_file.write(message)

            self.put_file(data_meta, path)
        finally:
            shutil.rmtree(tmpdir)

    def get_file(self, from_path, to_path):
        LOG.info("ftp get_file from_path=%s to_path=%s" % (from_path, to_path))
        try:
            dir = self.ftp.pwd()
            LOG.info("ftp get file dir %s" % dir)
        except (ftplib.all_errors, socket.error) as e:
            LOG.info("ftp get file failed %s try again" % e)
            self.init()
        try:
            file = open(to_path, 'wb')
            msg = self.ftp.retrbinary('RETR ' + from_path,
                                      file.write, 8192)
            # 226
            LOG.info("FTP GET %s, ret=%s" % (from_path, msg))
        except ftplib.all_errors as e:
            file.close()
            self.ftp.quit()
            LOG.info("ftp get file error %s" % e)
            raise e
        file.close()

    def put_file(self, from_path, to_path):
        LOG.info("ftp put_file from_path=%s to_path=%s" % (from_path, to_path))
        try:
            dir = self.ftp.pwd()
            LOG.info("ftp put file dir %s" % dir)
        except (ftplib.all_errors, socket.error) as e:
            LOG.info("ftp put file failed %s try again" % e)
            self.init()
        try:
            file = open(from_path, 'rb')
            msg = self.ftp.storbinary('STOR ' + to_path,
                                      file, 8192)
            # 226
            LOG.info("FTP PUT %s, ret=%s" % (from_path, msg))
        except ftplib.all_errors as e:
            self.ftp.quit()
            LOG.info("ftp put file error %s" % e)
            raise e
        file.close()

    def listdir(self, directory):
        LOG.info("ftp listdir directory=%s" % directory)
        try:
            # paramiko SFTPClient.listdir_attr returns
            # directories in arbitarary order, so we should
            # sort results of this command
            ret = self.ftp.cwd(directory)
            LOG.info('ftp listdir cwd ret=%s' % ret)
            res = self.ftp.nlst()
            LOG.info('ftp listdir res=%s' % res)
            return sorted(res)
        except ftplib.error_perm as e:
            LOG.info("ftp listdir error %s" % e)
            if '550' in e[0]:
                return list()
            else:
                raise

    def open(self, path, mode):
        pass

    def backup_blocks(self, backup):
        LOG.info("ftp backup_blocks ")
        self.init()
        # should recreate ssh for new process
        tmpdir = self._create_tempdir()
        try:
            data = utils.path_join(tmpdir, "data")
            LOG.info("backup_blocksa datadown=%s" % data)
            self.get_file(backup.data_path, data)
            with open(data, 'rb') as backup_file:
                while True:
                    chunk = backup_file.read(self.max_segment_size)
                    if chunk == '':
                        break
                    if len(chunk):
                        yield chunk
        finally:
            shutil.rmtree(tmpdir)

    def add_stream(self, stream, package_name, headers=None):
        """
        :param stream: data
        :param package_name: path
        :param headers: backup metadata information
        :return:
        """
        tmpdir = self._create_tempdir()
        LOG.info('add stream')
        try:
            split = package_name.rsplit('/', 1)
            # create backup_basedir
            backup_basedir = "{0}/{1}".format(self.storage_path,
                                              package_name)
            self.create_dirs(backup_basedir)
            # define backup_data_name
            backup_basepath = "{0}/{1}".format(backup_basedir,
                                               split[0])
            backup_metadata = "%s/metadata" % backup_basedir
            # write backup to backup_basepath
            data_backup = utils.path_join(tmpdir, "data_backup")
            with open(data_backup, 'wb') as backup_file:
                for el in stream:
                    backup_file.write(el)
            self.put_file(data_backup, backup_basepath)
            # write data matadata to backup_metadata
            metadata = utils.path_join(tmpdir, "metadata")
            with open(metadata, 'wb') as backup_meta:
                backup_meta.write(json.dumps(headers))
            self.put_file(metadata, backup_metadata)
        finally:
            shutil.rmtree(tmpdir)


class FtpStorage(BaseFtpStorage):
    """
    :type ftp: ftplib.FTP()
    """
    _type = 'ftp'

    def __init__(self, storage_path, remote_pwd,
                 remote_username, remote_ip, port, max_segment_size):
        """
            :param storage_path: directory of storage
            :type storage_path: str
            :return:
            """
        super(FtpStorage, self).__init__(storage_path,
                                         remote_pwd,
                                         remote_username,
                                         remote_ip,
                                         port,
                                         max_segment_size)

    def init(self):
        try:
            ftp = ftplib.FTP()
            ftp.set_pasv(True)
            # socket.setdefaulttimeout(60)
            ftp.connect(self.remote_ip, self.port, 60)
            ftp.login(self.remote_username, self.remote_pwd)
            nfiles = ftp.nlst()
            LOG.info("ftp nlst result=%s" % nfiles)
        except socket.error as e:
            LOG.info("ftp socket error=%s" % e)
            ftp.set_pasv(False)
        except ftplib.all_errors as e:  # socket.error
            msg = "create ftp failed error=%s" % e
            LOG.info(msg)
            raise Exception(msg)
        # we should keep link to ssh to prevent garbage collection
        self.ftp = ftp


class FtpsStorage(BaseFtpStorage):
    """
    :type ftps: ftplib.FTP_TLS()
    """
    _type = 'ftps'

    def __init__(self, storage_path, remote_pwd,
                 remote_username, remote_ip, port, max_segment_size,
                 keyfile, certfile):
        """
            :param storage_path: directory of storage
            :type storage_path: str
            :return:
            """
        self.keyfile = keyfile
        self.certfile = certfile
        LOG.info("key=%s cer=%s" % (self.keyfile, self.certfile))
        super(FtpsStorage, self).__init__(storage_path, remote_pwd,
                                          remote_username, remote_ip,
                                          port, max_segment_size)

    def init(self):
        try:
            ftps = ftplib.FTP_TLS(keyfile=self.keyfile,
                                  certfile=self.certfile)
            ftps.set_pasv(True)
            ftps.connect(self.remote_ip, self.port, 60)
            ftps.login(self.remote_username, self.remote_pwd)
            msg = ftps.prot_p()
            LOG.info("ftps encrypt %s, ret=%s" % (self.remote_ip, msg))
            nfiles = ftps.nlst()
            LOG.info("ftps nlst result=%s" % nfiles)
        except socket.error as e:
            LOG.info("ftps socket error=%s" % e)
            ftps.set_pasv(False)
        except ftplib.all_errors as e:
            msg = "create ftps failed error=%s" % e
            LOG.info(msg)
            raise Exception(msg)
        self.ftp = ftps
