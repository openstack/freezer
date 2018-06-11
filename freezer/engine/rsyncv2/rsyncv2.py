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


"""
Freezer rsync incremental engine
"""

import fnmatch
import getpass
import grp
import os
import pwd
import shutil
import stat
import sys
import threading

import msgpack
from oslo_log import log
import six

from six.moves import queue

from freezer.engine import engine
from freezer.engine.rsyncv2 import pyrsync
from freezer.utils import compress
from freezer.utils import crypt
from freezer.utils import winutils

LOG = log.getLogger(__name__)

# Version of the meta data structure format
RSYNC_DATA_STRUCT_VERSION = 2


class Rsyncv2Engine(engine.BackupEngine):
    def __init__(self, **kwargs):
        self.compression_algo = kwargs.get('compression')
        self.encrypt_pass_file = kwargs.get('encrypt_key', None)
        self.dereference_symlink = kwargs.get('symlinks')
        self.exclude = kwargs.get('exclude')
        self.storage = kwargs.get('storage')
        self.is_windows = winutils.is_windows()
        self.dry_run = kwargs.get('dry_run', False)
        self.max_segment_size = kwargs.get('max_segment_size')
        self.rsync_block_size = kwargs.get('rsync_block_size')
        self.fixed_blocks = 0
        self.modified_blocks = 0
        super(Rsyncv2Engine, self).__init__(storage=kwargs.get('storage'))

    @property
    def name(self):
        return "rsync"

    def metadata(self, *args):
        return {
            "engine_name": self.name,
            "compression": self.compression_algo,
            "rsync_block_size": self.rsync_block_size,
            # the encrypt_pass_file might be key content so we need to convert
            # to boolean
            "encryption": bool(self.encrypt_pass_file)
        }

    def backup_data(self, backup_path, manifest_path):
        """Execute backup using rsync algorithm.

        If an existing rsync meta data for file is available - the backup
        will be incremental, otherwise will be executed a level 0 backup.

        :param backup_path: Path to backup
        :param manifest_path: Path to backup metadata
        """

        LOG.info('Starting Rsync engine backup stream')
        LOG.info('Recursively archiving and compressing files '
                 'from {}'.format(os.getcwd()))

        file_read_limit = 0
        data_chunk = b''
        max_seg_size = self.max_segment_size

        # Initialize objects for compressing and encrypting data
        compressor = compress.Compressor(self.compression_algo)
        cipher = None
        if self.encrypt_pass_file:
            cipher = crypt.AESEncrypt(self.encrypt_pass_file)
            yield cipher.generate_header()

        write_queue = queue.Queue(maxsize=2)

        # Create thread for compute file signatures and read data
        t_get_sign_delta = threading.Thread(target=self.get_sign_delta,
                                            args=(
                                                backup_path, manifest_path,
                                                write_queue))
        t_get_sign_delta.daemon = True
        t_get_sign_delta.start()

        # Get backup data from queue
        while True:
            file_block = write_queue.get()

            if file_block is False:
                break

            block_len = len(file_block)
            if block_len == 0:
                continue

            data_chunk += file_block
            file_read_limit += block_len
            if file_read_limit >= max_seg_size:
                yield self._process_backup_data(data_chunk, compressor, cipher)
                data_chunk = b''
                file_read_limit = 0

        flushed_data = self._flush_backup_data(data_chunk, compressor, cipher)

        # Upload segments smaller then max_seg_size
        if len(flushed_data) < max_seg_size:
            yield flushed_data

        # Rejoining thread
        t_get_sign_delta.join()

        LOG.info("Rsync engine backup stream completed")

    @staticmethod
    def _flush_backup_data(data_chunk, compressor, cipher):
        flushed_data = b''
        if data_chunk:
            flushed_data += compressor.compress(data_chunk)

        flushed_data += compressor.flush()
        if flushed_data and cipher:
            flushed_data = cipher.encrypt(flushed_data)

        return flushed_data

    def restore_level(self, restore_path, read_pipe, backup, except_queue):
        """Restore the provided backup into restore_abs_path.

        Decrypt backup content if encrypted.
        Freezer rsync header data structure::

            [ {
                'path': '' (path to file),
                'inode': {
                    'mode': st_mode,
                    'dev': st_dev,
                    'uname': username,
                    'gname': groupname,
                    'atime': st_atime,
                    'mtime': st_mtime,
                    'size': st_size
                } (optional if file removed),
               'lname': 'link_name' (optional if symlink),
               'prev_name': '' (optional if renamed),
               'new_level': True (optional if incremental),
               'deleted': True (optional if removed),
               'deltas': len_of_blocks, [modified blocks] (if patch)
              },
              ...
            ]

        :param restore_path: Path where to restore file(s)
        :param read_pipe: ackup data
        :param backup: Backup info
        :param except_queue: Queue for exceptions
        """

        try:
            metadata = backup.metadata()
            if (not self.encrypt_pass_file and
                    metadata.get("encryption", False)):
                raise Exception("Cannot restore encrypted backup without key")

            self.compression_algo = metadata.get('compression',
                                                 self.compression_algo)

            if not os.path.exists(restore_path):
                raise ValueError(
                    'Provided restore path does not exist: {0}'.format(
                        restore_path))

            if self.dry_run:
                restore_path = '/dev/null'

            data_gen = self._restore_data(read_pipe)

            try:
                data_stream = data_gen.next()
                files_meta, data_stream = self._load_files_meta(data_stream,
                                                                data_gen)

                for fm in files_meta:
                    data_stream = self._restore_file(
                        fm, restore_path, data_stream, data_gen, backup.level)
            except StopIteration:
                LOG.info('Rsync restore process completed')
        except Exception as e:
            LOG.exception(e)
            except_queue.put(e)
            raise

    @staticmethod
    def _load_files_meta(data_stream, data_gen):
        files_meta = []
        while True:
            try:
                files_meta = msgpack.load(data_stream)
            except msgpack.ExtraData as e:
                files_meta = e.unpacked
                data_stream = six.BytesIO(e.extra)
                break
            except msgpack.OutOfData:
                data_stream.write(data_gen.next().read())
                data_stream.seek(0)
            else:
                break
        return files_meta, data_stream

    @staticmethod
    def _remove_file(file_abs_path):
        try:
            if os.path.isdir(file_abs_path):
                shutil.rmtree(file_abs_path)
            else:
                os.unlink(file_abs_path)
        except Exception as e:
            LOG.warning('[*] File or directory unlink error {}'.format(e))

    def _restore_file(self, file_meta, restore_path, data_stream, data_gen,
                      backup_level):
        file_abs_path = os.path.join(restore_path, file_meta['path'])

        inode = file_meta.get('inode', {})
        file_mode = inode.get('mode')

        if os.path.exists(file_abs_path):
            if backup_level == 0:
                self._remove_file(file_abs_path)
            else:
                if file_meta.get('deleted'):
                    self._remove_file(file_abs_path)
                    return data_stream
                elif file_meta.get('new_level') and not stat.S_ISREG(
                        file_mode):
                    self._set_inode(file_abs_path, inode)
                    return data_stream

        if not file_mode:
            return data_stream

        if stat.S_ISREG(file_mode):
            data_stream = self._restore_reg_file(file_abs_path, file_meta,
                                                 data_gen, data_stream)

        elif stat.S_ISDIR(file_mode):
            try:
                os.makedirs(file_abs_path, file_mode)
            except (OSError, IOError) as error:
                LOG.warning(
                    'Directory {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif stat.S_ISBLK(file_mode):
            try:
                self._make_dev_file(file_abs_path, file_meta['dev'], file_mode)
            except (OSError, IOError) as error:
                LOG.warning(
                    'Block file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif stat.S_ISCHR(file_mode):
            try:
                self._make_dev_file(file_abs_path, file_meta['dev'], file_mode)
            except (OSError, IOError) as error:
                LOG.warning(
                    'Character file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif stat.S_ISFIFO(file_mode):
            try:
                os.mkfifo(file_abs_path)
            except (OSError, IOError) as error:
                LOG.warning(
                    'FIFO or Pipe file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif stat.S_ISLNK(file_mode):
            try:
                os.symlink(file_meta.get('lname', ''), file_abs_path)
            except (OSError, IOError) as error:
                LOG.warning('Link file {0} creation error: {1}'.format(
                    file_abs_path, error))

        if not stat.S_ISLNK(file_mode):
            self._set_inode(file_abs_path, inode)

        return data_stream

    @staticmethod
    def _make_dev_file(file_abs_path, dev, mode):
        devmajor = os.major(dev)
        devminor = os.minor(dev)
        new_dev = os.makedev(devmajor, devminor)
        os.mknod(file_abs_path, mode, new_dev)

    @staticmethod
    def _create_reg_file(path, size, data_gen, data_stream):
        with open(path, 'wb') as fd:
            while fd.tell() < size:
                data = data_stream.read(size - fd.tell())
                if not data:
                    data_stream = data_gen.next()
                    continue
                fd.write(data)

        return data_stream

    def _restore_data(self, read_pipe):
        try:
            data_chunk = read_pipe.recv_bytes()
            decompressor = compress.Decompressor(self.compression_algo)
            decryptor = None

            if self.encrypt_pass_file:
                decryptor = crypt.AESDecrypt(self.encrypt_pass_file,
                                             data_chunk[:crypt.BS])
                data_chunk = data_chunk[crypt.BS:]

            while True:
                try:
                    data_chunk = self._process_restore_data(
                        data_chunk, decompressor, decryptor)
                except Exception:
                    data_chunk += read_pipe.recv_bytes()
                    continue
                if data_chunk:
                    yield six.BytesIO(data_chunk)
                data_chunk = read_pipe.recv_bytes()

        except EOFError:
            LOG.info("[*] EOF from pipe. Flushing buffer.")
            data_chunk = decompressor.flush()
            if data_chunk:
                yield six.BytesIO(data_chunk)

    @staticmethod
    def _process_backup_data(data, compressor, encryptor, do_compress=True):
        """Compresses and encrypts provided data according to args"""

        if do_compress:
            data = compressor.compress(data)

        if encryptor:
            data = encryptor.encrypt(data)
        return data

    @staticmethod
    def _process_restore_data(data, decompressor, decryptor):
        """Decrypts and decompresses provided data according to args"""

        if decryptor:
            data = decryptor.decrypt(data)

        data = decompressor.decompress(data)
        return data

    def _get_deltas_info(self, file_name, old_file_meta):
        len_deltas = 0
        old_signature = old_file_meta['signature']
        rsync_bs = self.rsync_block_size

        # Get changed blocks index only
        index = 0
        modified_blocks = []
        with open(file_name, 'rb') as fd:
            for block_index in pyrsync.rsyncdelta_fast(
                    fd,
                    (old_signature[0], old_signature[1]),
                    rsync_bs):

                if not isinstance(block_index, int):
                    block_len = len(block_index)
                    if block_len > 0:
                        len_deltas += block_len
                        modified_blocks.append(index)
                        self.modified_blocks += 1
                else:
                    self.fixed_blocks += 1

                index += 1

        return len_deltas, modified_blocks

    def _backup_deltas(self, file_header, write_queue):
        _, modified_blocks = file_header['deltas']
        rsync_bs = self.rsync_block_size
        with open(file_header['path'], 'rb') as fd:
            for block_index in modified_blocks:
                offset = block_index * rsync_bs
                fd.seek(offset)
                data_block = fd.read(rsync_bs)
                write_queue.put(data_block)

    @staticmethod
    def _is_file_modified(old_inode, inode):
        """Check for changes on inode or file data

        :param old_inode: meta data of the previous backup execution
        :param inode: meta data of the current backup execution
        :return: True if the file changed, False otherwise
        """

        # Check if new ctime/mtime is different from the current one
        file_change_flag = None
        if old_inode['mtime'] != inode['mtime']:
            file_change_flag = True
        elif old_inode['ctime'] != inode['ctime']:
            file_change_flag = True

        return file_change_flag

    def _patch_reg_file(self, file_path, size, data_stream, data_gen,
                        deltas_info):
        len_deltas, modified_blocks = deltas_info
        rsync_bs = self.rsync_block_size
        if len_deltas:
            reminder = len_deltas % rsync_bs
            last_block = modified_blocks.pop()
            # Get all the block index offset from
            with open(file_path, 'rb+') as fd:
                for block_index in modified_blocks:
                    data_stream = self._patch_block(
                        fd, block_index, data_stream, data_gen,
                        rsync_bs, rsync_bs)

                data_stream = self._patch_block(
                    fd, last_block, data_stream, data_gen,
                    reminder if reminder else rsync_bs, rsync_bs)

                fd.truncate(size)

        return data_stream

    @staticmethod
    def _patch_block(fd, block_index, data_stream, data_gen, size, bs):
        offset = block_index * bs
        fd.seek(offset)

        data_stream_pos = data_stream.tell()
        while (data_stream.len - data_stream.tell()) < size:
            data_stream.write(data_gen.next().read())
            data_stream.flush()
            data_stream.seek(data_stream_pos)

        fd.write(data_stream.read(size))
        return data_stream

    def _restore_reg_file(self, file_path, file_meta, data_gen, data_chunk):
        """Create the regular file and write data on it.

        :param size:
        :param file_path:
        :param file_meta:
        :param data_gen:
        :param data_chunk:
        :return:
        """

        new_level = file_meta.get('new_level', False)
        deltas = file_meta.get('deltas')
        size = file_meta['inode']['size']
        if new_level and deltas:
            return self._patch_reg_file(file_path, size, data_chunk,
                                        data_gen, deltas)
        else:
            return self._create_reg_file(file_path, size,
                                         data_gen, data_chunk)

    @staticmethod
    def _set_inode(file_path, inode):
        """Set the file inode fields according to the provided args.

        :param file_path:
        :param inode:
        :return:
        """

        try:
            set_uid = pwd.getpwnam(inode['uname']).pw_uid
            set_gid = grp.getgrnam(inode['gname']).gr_gid
        except (IOError, OSError):
            try:
                set_uid = pwd.getpwnam(getpass.getuser()).pw_uid
                set_gid = grp.getgrnam(getpass.getuser()).gr_gid
            except (OSError, IOError) as err:
                raise Exception(err)
        try:
            os.chown(file_path, set_uid, set_gid)
            os.chmod(file_path, inode['mode'])
            os.utime(file_path, (inode['atime'], inode['mtime']))
        except (OSError, IOError):
            LOG.warning(
                '[*] Unable to set inode info for {}'.format(file_path))

    @staticmethod
    def _parse_file_stat(os_stat):
        header_meta = {
            'mode': os_stat.st_mode,
            'dev': os_stat.st_dev,
            'uname': pwd.getpwuid(os_stat.st_uid).pw_name,
            'gname': grp.getgrgid(os_stat.st_gid).gr_name,
            'atime': os_stat.st_atime,
            'mtime': os_stat.st_mtime,
            'size': os_stat.st_size
        }

        incremental_meta = {
            'mode': os_stat.st_mode,
            'ctime': os_stat.st_ctime,
            'mtime': os_stat.st_mtime
        }

        return header_meta, incremental_meta

    def _get_file_stat(self, rel_path):
        """Generate file meta data from file path.

        Return the meta data as a two dicts: header and incremental

        :param rel_path: related file path
        :return: file meta as a two dicts
        """

        # Get file inode information
        try:
            os_stat = os.lstat(rel_path)
        except (OSError, IOError) as error:
            raise Exception('[*] Error on file stat: {}'.format(error))

        return self._parse_file_stat(os_stat)

    def _backup_file(self, file_path, write_queue):
        max_seg_size = self.max_segment_size
        with open(file_path, 'rb') as file_path_fd:
            data_block = file_path_fd.read(max_seg_size)

            while data_block:
                write_queue.put(data_block)
                data_block = file_path_fd.read(max_seg_size)

    @staticmethod
    def _find_same_inode(file_path, old_files):
        """Find same file meta data for given file name.

        Return the same file name in incremental info if file was removed.

        :param file_path: related file path
        :return: the same file name
        """

        file_name = os.path.basename(file_path)
        for fn in six.iterkeys(old_files):
            base_name = os.path.basename(fn)
            if fnmatch.fnmatch(base_name, '*' + file_name + '*'):
                return base_name
        return None

    @staticmethod
    def _get_old_file_meta(file_path, file_stat, old_fs_meta_struct):
        old_file_meta = None
        prev_name = None
        if old_fs_meta_struct:
            try:
                old_file_meta = old_fs_meta_struct[file_path]
                new_mode = file_stat['mode']
                old_mode = old_file_meta['mode']
                if new_mode != old_mode:
                    old_file_meta = None
            except KeyError:
                pass

        return old_file_meta, prev_name

    def _prepare_file_info(self, file_path, old_fs_meta_struct):
        file_stat, file_meta = self._get_file_stat(file_path)
        file_mode = file_stat['mode']

        if stat.S_ISSOCK(file_mode):
            return None, None

        file_header = {'path': file_path, 'inode': file_stat}

        if stat.S_ISLNK(file_mode):
            file_header['lname'] = os.readlink(file_path)

        old_file_meta, old_name = self._get_old_file_meta(
            file_path, file_stat, old_fs_meta_struct)
        if old_name:
            file_header['prev_name'] = old_name

        if old_file_meta:
            if self._is_file_modified(old_file_meta, file_meta):
                file_header['new_level'] = True
            else:
                return old_file_meta, None

        if not stat.S_ISREG(file_mode):
            return file_meta, file_header

        if old_file_meta:
            len_deltas, mod_blocks = self._get_deltas_info(file_path,
                                                           old_file_meta)
            if len_deltas:
                file_header['deltas'] = (len_deltas, mod_blocks)

        return file_meta, file_header

    def _get_file_meta(self, fn, fs_path, old_fs_meta_struct, files_meta,
                       files_header, counts):
        file_path = os.path.relpath(fn, fs_path)
        header_append = files_header.append
        counts['backup_size_on_disk'] += os.path.getsize(file_path)
        meta, header = self._prepare_file_info(file_path, old_fs_meta_struct)
        if meta:
            files_meta['files'][file_path] = meta
        if header:
            header_append(header)

    def _backup_reg_file(self, backup_meta, write_queue):
        if backup_meta.get('deltas'):
            self._backup_deltas(backup_meta, write_queue)
        else:
            self._backup_file(backup_meta['path'], write_queue)

    def get_sign_delta(self, fs_path, manifest_path, write_queue):
        """Compute the file or fs tree path signatures.

        Return blocks of changed data.

        :param fs_path:
        :param manifest_path:
        :param write_queue:
        :return:
        """

        files_meta = {
            'files': {},
            'platform': sys.platform,
            'abs_backup_path': os.getcwd(),
            'rsync_struct_ver': RSYNC_DATA_STRUCT_VERSION,
            'rsync_block_size': self.rsync_block_size}

        counts = {
            'total_files': 0,
            'total_dirs': 0,
            'backup_size_on_disk': 0,
        }

        # Get old file meta structure or an empty dict if not available
        old_fs_meta_struct, rsync_bs = self.get_fs_meta_struct(manifest_path)
        if rsync_bs and rsync_bs != self.rsync_block_size:
            LOG.warning('[*] Incremental backup will be performed '
                        'with rsync_block_size={}'.format(rsync_bs))
            self.rsync_block_size = rsync_bs

        backup_header = []

        # Grab list of all files and directories
        exclude = self.exclude
        if os.path.isdir(fs_path):
            for dn, dl, fl in os.walk(fs_path):
                for dir_name in dl:
                    self._get_file_meta(os.path.join(dn, dir_name),
                                        fs_path, old_fs_meta_struct,
                                        files_meta, backup_header, counts)
                    counts['total_dirs'] += 1

                if exclude:
                    fl = (fn for fn in fl if not fnmatch.fnmatch(fn, exclude))

                for fn in fl:
                    self._get_file_meta(os.path.join(dn, fn), fs_path,
                                        old_fs_meta_struct, files_meta,
                                        backup_header, counts)
                    counts['total_files'] += 1
        else:
            self._get_file_meta(fs_path, os.getcwd(), old_fs_meta_struct,
                                files_meta, backup_header, counts)
            counts['total_files'] += 1

        # Check for deleted files
        for del_file in (f for f in six.iterkeys(old_fs_meta_struct) if
                         f not in files_meta['files']):
            backup_header.append({'path': del_file, 'deleted': True})

        # Write backup header
        write_queue.put(msgpack.dumps(backup_header))

        # Backup reg files
        reg_files = (f for f in backup_header if f.get('inode') and
                     stat.S_ISREG(f['inode']['mode']))

        for reg_file in reg_files:
            self._backup_reg_file(reg_file, write_queue)
            self._compute_checksums(reg_file['path'],
                                    files_meta['files'][reg_file['path']])

        LOG.info("Backup session metrics: {0}".format(counts))
        LOG.info("Count of modified blocks %s, count of fixed blocks %s" % (
            self.modified_blocks, self.fixed_blocks))

        self.write_engine_meta(manifest_path, files_meta)

        # Put False on the queue so it will be terminated on the other side:
        write_queue.put(False)

    def write_engine_meta(self, manifest_path, files_meta):
        # Compress meta data file
        # Write meta data to disk as JSON
        with open(manifest_path, 'wb') as manifest_file:
            cmp_meta = compress.one_shot_compress(
                self.compression_algo, msgpack.dumps(files_meta))
            manifest_file.write(cmp_meta)

    def get_fs_meta_struct(self, fs_meta_path):
        old_files_meta = {}

        if os.path.isfile(fs_meta_path):
            with open(fs_meta_path) as meta_file:
                old_files_meta = msgpack.loads(compress.one_shot_decompress(
                    self.compression_algo, meta_file.read()))

        old_fs_meta_struct = old_files_meta.get('files', {})
        rsync_bs = old_files_meta.get('rsync_block_size')

        return old_fs_meta_struct, rsync_bs

    def _compute_checksums(self, rel_path, file_meta):
        # Files type where the file content can be backed up
        args = (rel_path, self.rsync_block_size)
        file_meta['signature'] = pyrsync.blockchecksums(args)
