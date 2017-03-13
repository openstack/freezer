"""Freezer rsync incremental engine

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

import getpass
import grp
import json
import os
import pwd
import Queue
import re
import stat
import sys
import threading

from oslo_log import log
from six.moves import cStringIO

from freezer.engine import engine
from freezer.engine.rsync import pyrsync
from freezer.utils import compress
from freezer.utils import crypt
from freezer.utils import winutils

LOG = log.getLogger(__name__)

# Data block size of used by rsync to generate signature
RSYNC_BLOCK_SIZE = 4096
# Version of the meta data structure format
RSYNC_DATA_STRUCT_VERSION = 1
# Rsync main block size for streams, 32MB (1024*1024*32)
RSYNC_BLOCK_BUFF_SIZE = 33554432
# Files type where file data content can be backed up or restored
REG_FILE = ('r', 'u')


class RsyncEngine(engine.BackupEngine):

    def __init__(
            self, compression, symlinks, exclude, storage,
            max_segment_size, encrypt_key=None,
            dry_run=False):
        self.compression_algo = compression
        self.encrypt_pass_file = encrypt_key
        self.dereference_symlink = symlinks
        self.exclude = exclude
        self.storage = storage
        self.is_windows = winutils.is_windows()
        self.dry_run = dry_run
        self.max_segment_size = max_segment_size
        # Compression and encryption objects
        self.compressor = None
        self.cipher = None
        super(RsyncEngine, self).__init__(storage=storage)

    @property
    def name(self):
        return "rsync"

    def metadata(self, *args):
        return {
            "engine_name": self.name,
            "compression": self.compression_algo,
            # the encrypt_pass_file might be key content so we need to convert
            # to boolean
            "encryption": bool(self.encrypt_pass_file)
        }

    def backup_data(self, backup_resource, manifest_path):
        """Execute backup using rsync algorithm.

        If an existing rsync meta data is available the backup
        will be incremental, otherwise will be executed a level 0 backup

        :param backup_resource:
        :param manifest_path:
        :return:
        """

        LOG.info("Starting RSYNC engine backup data stream")

        file_read_limit = 0
        data_chunk = b''
        LOG.info(
            'Recursively archiving and compressing files from {}'.format(
                os.getcwd()))

        self.compressor = compress.Compressor(self.compression_algo)

        if self.encrypt_pass_file:
            self.cipher = crypt.AESEncrypt(self.encrypt_pass_file)
            data_chunk += self.cipher.generate_header()

        rsync_queue = Queue.Queue(maxsize=2)

        t_get_sign_delta = threading.Thread(
            target=self.get_sign_delta,
            args=(
                backup_resource, manifest_path, rsync_queue))
        t_get_sign_delta.daemon = True

        t_get_sign_delta.start()

        while True:
            file_block = rsync_queue.get()

            if file_block is False:
                break
            if len(file_block) == 0:
                continue

            data_chunk += file_block
            file_read_limit += len(file_block)
            if file_read_limit >= self.max_segment_size:
                yield data_chunk
                data_chunk = b''
                file_read_limit = 0

        # Upload segments smaller then max_segment_size
        if len(data_chunk) < self.max_segment_size:
            yield data_chunk

        # Rejoining thread
        t_get_sign_delta.join()

    def restore_level(self, restore_resource, read_pipe, backup, except_queue):
        """Restore the provided file into restore_abs_path.

        Decrypt the file if backup_opt_dict.encrypt_pass_file key is provided.
        Freezer rsync header data structure:

            header_len, RSYNC_DATA_STRUCT_VERSION, file_mode,
            os_stat.st_uid, os_stat.st_gid, os_stat.st_size,
            mtime, ctime, uname, gname, file_type, linkname

        :param restore_resource:
        :param read_pipe:
        :param backup:
        :param except_queue:
        :return:
        """
        try:
            metadata = backup.metadata()
            if (not self.encrypt_pass_file and
                    metadata.get("encryption", False)):
                raise Exception("Cannot restore encrypted backup without key")

            self.compression_algo = metadata.get('compression',
                                                 self.compression_algo)

            if not os.path.exists(restore_resource):
                raise ValueError(
                    'Provided restore path does not exist: {0}'.format(
                        restore_resource))

            if self.dry_run:
                restore_resource = '/dev/null'

            raw_data_chunk = read_pipe.recv_bytes()

            self.compressor = compress.Decompressor(self.compression_algo)

            if self.encrypt_pass_file:
                self.cipher = crypt.AESDecrypt(self.encrypt_pass_file,
                                               raw_data_chunk[:16])
                raw_data_chunk = raw_data_chunk[16:]

            data_chunk = self.process_restore_data(raw_data_chunk)

            header_str = r'^(\d{1,})\00'
            flushed = False
            while True:
                header_match = re.search(header_str, data_chunk)
                if not header_match and not flushed:
                    try:
                        data_chunk += self.process_restore_data(
                            read_pipe.recv_bytes())
                        continue
                    except EOFError:
                        LOG.info("EOFError: Pipe closed. Flushing buffer...")
                        data_chunk += self.compressor.flush()
                        flushed = True

                if data_chunk and header_match:
                    header_len = int(header_match.group(1))
                    if header_len > len(data_chunk) and not flushed:
                        try:
                            data_chunk += self.process_restore_data(
                                read_pipe.recv_bytes())
                        except EOFError:
                            LOG.info("[*] End of File: Pipe closed. "
                                     "Flushing the buffer.")
                            data_chunk += self.compressor.flush()
                            flushed = True

                    header = data_chunk[:header_len]
                    header_list = header.split('\00')
                    data_chunk = data_chunk[header_len:]
                    data_chunk = self.make_files(
                        header_list, restore_resource, read_pipe,
                        data_chunk, flushed, backup.level)
                else:
                    LOG.info('No more data available...')
                    break
        except Exception as e:
            LOG.exception(e)
            except_queue.put(e)
            raise

    def process_backup_data(self, data, do_compress=True):
        """Compresses and encrypts provided data according to args"""

        if do_compress:
            data = self.compressor.compress(data)

        if self.encrypt_pass_file:
            data = self.cipher.encrypt(data)
        return data

    def process_restore_data(self, data):
        """Decrypts and decompresses provided data according to args"""

        if self.encrypt_pass_file:
            data = self.cipher.decrypt(data)

        data = self.compressor.decompress(data)
        return data

    @staticmethod
    def rsync_gen_delta(file_path_fd, old_file_meta):
        """Get rsync delta for file descriptor provided as arg.

        :param file_path_fd:
        :param old_file_meta:
        :return:
        """

        if not old_file_meta:
            raise StopIteration

        # If the ctime or mtime has changed, the delta is computed
        # data block is returned

        len_deltas = 0
        old_signature = old_file_meta['signature']
        # Get changed blocks index only
        all_changed_indexes = cStringIO()
        file_path_fd.seek(0)
        previous_index = -1
        modified_blocks = []
        for block_index in pyrsync.rsyncdelta(
                file_path_fd,
                (old_signature[0], old_signature[1]),
                RSYNC_BLOCK_SIZE):

            previous_index += 1

            if not isinstance(block_index, int):
                len_deltas += len(block_index)
                all_changed_indexes.write(b'\00{}'.format(previous_index))
                modified_blocks.append(previous_index)

        # Yield the total length data changed blocks

        yield b'\00' + str(len_deltas)
        previous_index_str = all_changed_indexes.getvalue() + b'\00'
        len_previous_index_str = len(previous_index_str) + 1
        # Yield the length of the string that contain all the indexes

        yield b'\00' + str(len_previous_index_str) + b'\00'
        # Yield string containing all the indexes separated by \00

        yield previous_index_str

        # Get blocks of changed data
        file_path_fd.seek(0)
        for block_index in modified_blocks:
            offset = block_index * RSYNC_BLOCK_SIZE
            file_path_fd.seek(offset)
            data_block = file_path_fd.read(RSYNC_BLOCK_SIZE)

            yield data_block

    @staticmethod
    def is_file_modified(old_file_meta, file_meta):
        """Check for changes on inode or file data

        :param old_file_meta: meta data of the previous backup execution
        :param file_meta: meta data of the current backup execution
        :return: True if the file changed, False otherwise
        """

        # Get mtime and ctime from previous backup execution
        old_file_mtime = old_file_meta['inode']['mtime']
        old_file_ctime = old_file_meta['inode']['ctime']
        fs_index_file_mtime = file_meta['inode']['mtime']
        fs_index_file_ctime = file_meta['inode']['ctime']

        # Check if new ctime/mtime is different from the current one
        file_change_flag = None
        if old_file_mtime != fs_index_file_mtime:
            file_change_flag = True
        elif old_file_ctime != fs_index_file_ctime:
            file_change_flag = True

        # TODO(raliev): There is also need to add check size of files
        return file_change_flag

    def write_file(self, file_fd, size, data_chunk, read_pipe, flushed):
        while size:
            written_data = min(len(data_chunk), size)
            file_fd.write(data_chunk[:written_data])
            data_chunk = data_chunk[written_data:]
            size -= written_data
            if size > 0 and not flushed:
                try:
                    data_chunk += self.process_restore_data(
                        read_pipe.recv_bytes())
                except EOFError:
                    LOG.info(
                        "[*] EOF from pipe. Flushing buffer.")
                    data_chunk += self.compressor.flush()
                    flushed = True
                    continue
            elif flushed:
                break
        return data_chunk

    def write_changes_in_file(self, fd_curr_file, data_chunk, read_pipe):
        # Searching for:
        # - the block incremental header string
        # - len of all the changed blocks
        # - len of the index string
        offset_match = re.search(r'^(\00(\d+?)\00(\d+?)\00)', data_chunk)

        if offset_match:
            offset_size = len(offset_match.group(1))
            len_deltas = int(offset_match.group(2))
            len_offset_str = int(offset_match.group(3)) - 1

            no_of_blocks, reminder = divmod(len_deltas, RSYNC_BLOCK_SIZE)
            if len_deltas > 0:
                block_indexes = (
                    data_chunk[offset_size: offset_size + len_offset_str])
                data_chunk = data_chunk[offset_size + len(block_indexes):]
                blocks_offsets = filter(None, block_indexes.split('\00'))
                # Get all the block index offset from
                for block_index in blocks_offsets:
                    while len(data_chunk) < RSYNC_BLOCK_SIZE:
                        try:
                            data_chunk += self.process_restore_data(
                                read_pipe.recv_bytes())
                        except EOFError:
                            LOG.info(
                                "[*] EOF from pipe. Flushing buffer.")
                            data_chunk += self.compressor.flush()
                            break

                    offset = int(block_index) * RSYNC_BLOCK_SIZE
                    fd_curr_file.seek(offset)
                    fd_curr_file.write(data_chunk[:RSYNC_BLOCK_SIZE])
                    data_chunk = data_chunk[RSYNC_BLOCK_SIZE:]

                if reminder:
                    fd_curr_file.write(data_chunk[:reminder])
                    data_chunk = data_chunk[reminder:]

        return data_chunk

    def make_reg_file(
            self, size, file_path, read_pipe, data_chunk,
            flushed, level_id):
        """Create the regular file and write data on it.

        :param size:
        :param file_path:
        :param read_pipe:
        :param data_chunk:
        :param flushed:
        :param level_id:
        :return:
        """

        # File is created. If size is 0, no content is written and the
        # function return

        if level_id == '0000':
            fd_curr_file = open(file_path, 'wb')
            data_chunk = self.write_file(fd_curr_file, size, data_chunk,
                                         read_pipe, flushed)
        elif level_id == '1111':
            fd_curr_file = open(file_path, 'rb+')
            data_chunk = self.write_changes_in_file(fd_curr_file,
                                                    data_chunk, read_pipe)
        fd_curr_file.close()
        return data_chunk

    def set_inode(self, uname, gname, mtime, name):
        """Set the file inode fields according to the provided args.

        :param uname:
        :param gname:
        :param mtime:
        :param name:
        :return:
        """

        try:
            current_uid = pwd.getpwnam(uname).pw_uid
            current_gid = grp.getgrnam(gname).gr_gid
            os.chown(name, current_uid, current_gid)
            os.utime(name, (mtime, mtime))
        except (IOError, OSError):
            try:
                current_uid = pwd.getpwnam(getpass.getuser()).pw_uid
                current_gid = grp.getgrnam(getpass.getuser()).gr_gid
                os.chown(name, current_uid, current_gid)
                os.utime(name, (mtime, mtime))
            except (OSError, IOError) as err:
                raise Exception(err)

    @staticmethod
    def get_file_type(file_mode, fs_path):
        """Extract file type from the the file mode retrieved
        from file abs path

        :param file_mode:
        :param fs_path:
        :return:
        """

        if stat.S_ISREG(file_mode):
            return 'r', ''
        if stat.S_ISDIR(file_mode):
            return 'd', ''
        if stat.S_ISLNK(file_mode):
            return 'l', os.readlink(fs_path)
        if stat.S_ISCHR(file_mode):
            return 'c', ''
        if stat.S_ISBLK(file_mode):
            return 'b', ''
        if stat.S_ISFIFO(file_mode):
            return 'p', ''
        if stat.S_ISSOCK(file_mode):
            return 's', ''

        return 'u', ''

    @staticmethod
    def gen_file_header(file_path, inode_str_struct):
        """Generate file header for rsync binary data file

        :param file_path: file path
        :param inode_str_struct: file binary string including inode data
        :return: chunk of binary data to be processed on the next iteration
        """

        start_of_block = b'\00{}\00'.format(file_path)
        header_size = len(start_of_block) + len(inode_str_struct)
        header_size += len(str(header_size))
        file_header = b'{}{}{}'.format(
            header_size, start_of_block, inode_str_struct)
        len_file_header = len(file_header)

        if header_size != len_file_header:
            file_header_list = file_header.split('\00')
            file_header_list = file_header_list[1:]
            file_header_list.insert(0, str(len_file_header))
            file_header = '\00'.join(file_header_list)
        return file_header

    def make_files(
            self, header_list, restore_abs_path, read_pipe,
            data_chunk, flushed,
            current_backup_level):
        """
        Header list binary structure:

        header_len, file_abs_path, RSYNC_DATA_STRUCT_VERSION, file_mode,
        os_stat.st_uid, os_stat.st_gid, os_stat.st_size,
        mtime, ctime, uname, gname, file_type, linkname, rsync_block_size,

        :param header_list:
        :param restore_abs_path:
        :param read_pipe:
        :param data_chunk:
        :param flushed:
        :param current_backup_level:
        :return:
        """

        # The following commented lines are important for development and
        # troubleshooting, please let it go :)
        # header_len = header_list[0]
        file_path = header_list[1]
        # data_ver = header_list[2]
        file_mode = header_list[3]
        # uid = header_list[4]
        # gid = header_list[5]
        size = header_list[6]
        mtime = header_list[7]
        # ctime = header_list[8]
        uname = header_list[9]
        gname = header_list[10]
        file_type = header_list[11]
        link_name = header_list[12]
        # inumber = header_list[13]
        # nlink = header_list[14]
        devminor = header_list[15]
        devmajor = header_list[16]
        # rsync_block_size = header_list[17]
        level_id = header_list[18]
        rm = header_list[19]

        # Data format conversion
        file_mode = int(file_mode)
        size = int(size)
        mtime = int(mtime)
        file_abs_path = '{0}/{1}'.format(restore_abs_path, file_path)

        if not os.path.isdir(file_abs_path) and os.path.exists(
                file_abs_path) and current_backup_level == 0:
            os.unlink(file_abs_path)

        if not os.path.isdir(file_abs_path) and os.path.exists(
                file_abs_path) and current_backup_level != 0 and rm == '1111':
            os.unlink(file_abs_path)
            return data_chunk

        if file_type in REG_FILE:
            data_chunk = self.make_reg_file(
                size, file_abs_path, read_pipe, data_chunk,
                flushed, level_id)

        elif file_type == 'd':
            try:
                os.makedirs(file_abs_path, file_mode)
            except (OSError, IOError) as error:
                if error.errno != 17:  # E_EXIST
                    LOG.warning(
                        'Directory {0} creation error: {1}'.format(
                            file_abs_path, error))

        elif file_type == 'b':
            file_mode |= stat.S_IFBLK
            try:
                devmajor = int(devmajor)
                devminor = int(devminor)
                new_dev = os.makedev(devmajor, devminor)
                os.mknod(file_abs_path, file_mode, new_dev)
            except (OSError, IOError) as error:
                LOG.warning(
                    'Block file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif file_type == 'c':
            file_mode |= stat.S_IFCHR
            try:
                devmajor = int(devmajor)
                devminor = int(devminor)
                new_dev = os.makedev(devmajor, devminor)
                os.mknod(file_abs_path, file_mode, new_dev)
            except (OSError, IOError) as error:
                LOG.warning(
                    'Character file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif file_type == 'p':
            try:
                os.mkfifo(file_abs_path)
            except (OSError, IOError) as error:
                LOG.warning(
                    'FIFO or Pipe file {0} creation error: {1}'.format(
                        file_abs_path, error))

        elif file_type == 'l':
            try:
                os.symlink(link_name, file_abs_path)
            except (OSError, IOError) as error:
                LOG.warning('Link file {0} creation error: {1}'.format(
                    file_abs_path, error))

        if file_type != 'l':
            self.set_inode(uname, gname, mtime, file_abs_path)

        return data_chunk

    def get_file_struct(self, fs_path, new_level=False):
        """Generate file meta data from file abs path.

        Return the meta data as a dict structure and a binary string

        :param fs_path: file abs path
        :param new_level
        :return: file data structure
        """

        # Get file inode information, whether the file is a regular
        # file or a symbolic link
        try:
            os_stat = os.lstat(fs_path)
        except (OSError, IOError) as error:
            raise Exception('[*] Error on file stat: {}'.format(error))

        file_mode = os_stat.st_mode
        # Get file type. If file type is a link it returns also the
        # file pointed by the link
        file_type, lname = self.get_file_type(file_mode, fs_path)

        # If file_type is a socket return False
        if file_type == 's':
            return False, False

        ctime = int(os_stat.st_ctime)
        mtime = int(os_stat.st_mtime)
        uname = pwd.getpwuid(os_stat.st_uid)[0]
        gname = grp.getgrgid(os_stat.st_gid)[0]

        dev = os_stat.st_dev
        inumber = os_stat.st_ino
        nlink = os_stat.st_nlink
        uid = os_stat.st_uid
        gid = os_stat.st_gid
        size = os_stat.st_size
        devmajor = os.major(dev)
        devminor = os.minor(dev)

        level_id = '0000'
        if new_level:
            level_id = '1111'

        # build file meta data as dictionary
        inode_dict = {
            'inode': {
                'inumber': inumber,
                'nlink': nlink,
                'mode': file_mode,
                'uid': uid,
                'gid': gid,
                'size': size,
                'devmajor': devmajor,
                'devminor': devminor,
                'mtime': mtime,
                'ctime': ctime,
                'uname': uname,
                'gname': gname,
                'ftype': file_type,
                'lname': lname,
                'rsync_block_size': RSYNC_BLOCK_SIZE,
                'level_id': level_id,
                'deleted': '0000'
            }
        }

        # build file meta data as binary string
        inode_bin_str = (
            b'{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}\00{}\00{}\00{}').format(
            RSYNC_DATA_STRUCT_VERSION, file_mode,
            uid, gid, size, mtime, ctime, uname, gname,
            file_type, lname, inumber, nlink, devminor, devmajor,
            RSYNC_BLOCK_SIZE, level_id, '0000')

        return inode_dict, inode_bin_str

    def gen_struct_for_deleted_files(self, files_meta, old_fs_meta_struct,
                                     rel_path, write_queue):
        files_meta['files'][rel_path] = old_fs_meta_struct['files'][rel_path]
        files_meta['files'][rel_path]['inode']['deleted'] = '1111'
        file_mode = files_meta['files'][rel_path]['inode']['mode']
        uid = files_meta['files'][rel_path]['inode']['uid']
        gid = files_meta['files'][rel_path]['inode']['gid']
        size = files_meta['files'][rel_path]['inode']['size']
        mtime = files_meta['files'][rel_path]['inode']['mtime']
        ctime = files_meta['files'][rel_path]['inode']['ctime']
        uname = files_meta['files'][rel_path]['inode']['uname']
        gname = files_meta['files'][rel_path]['inode']['gname']
        file_type = files_meta['files'][rel_path]['inode']['ftype']
        lname = files_meta['files'][rel_path]['inode']['lname']
        inumber = files_meta['files'][rel_path]['inode']['inumber']
        nlink = files_meta['files'][rel_path]['inode']['nlink']
        devminor = files_meta['files'][rel_path]['inode']['devminor']
        devmajor = files_meta['files'][rel_path]['inode']['devmajor']
        level_id = files_meta['files'][rel_path]['inode']['level_id']

        inode_bin_str = (
            b'{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}'
            b'\00{}\00{}\00{}\00{}\00{}\00{}\00{}\00{}').format(
            RSYNC_DATA_STRUCT_VERSION, file_mode,
            uid, gid, size, mtime, ctime, uname, gname,
            file_type, lname, inumber, nlink, devminor, devmajor,
            RSYNC_BLOCK_SIZE, level_id, '1111')
        file_header = self.gen_file_header(rel_path, inode_bin_str)
        compr_block = self.process_backup_data(file_header)
        write_queue.put(compr_block)

    def process_file(self, file_path, fs_path, files_meta,
                     old_fs_meta_struct, write_queue):
        rel_path = os.path.relpath(file_path, fs_path)

        new_level = True if self.get_old_file_meta(
            old_fs_meta_struct, rel_path) else False

        inode_dict_struct, inode_str_struct = self.get_file_struct(
            rel_path, new_level)

        if not inode_dict_struct:
            return

        if os.path.isdir(file_path):
            files_meta['directories'][file_path] = inode_dict_struct
            files_meta['meta']['backup_size_on_disk'] += os.path.getsize(
                rel_path)
            file_header = self.gen_file_header(rel_path, inode_str_struct)

            compressed_block = self.process_backup_data(file_header)
            files_meta['meta']['backup_size_compressed'] += len(
                compressed_block)
            write_queue.put(compressed_block)
        else:
            file_metadata = self.compute_incrementals(
                rel_path, inode_str_struct,
                inode_dict_struct, files_meta,
                old_fs_meta_struct, write_queue)

            files_meta.update(file_metadata)

    def get_sign_delta(self, fs_path, manifest_path, write_queue):
        """Compute the file or fs tree path signatures.

        :param fs_path:
        :param manifest_path
        :param write_queue:
        :return:
        """

        files_meta = {
            'files': {},
            'directories': {},
            'meta': {
                'broken_links_tot': '',
                'total_files': '',
                'total_directories': '',
                'backup_size_on_disk': 0,
                'backup_size_uncompressed': 0,
                'backup_size_compressed': 0,
                'platform': sys.platform
            },
            'abs_backup_path': os.getcwd(),
            'broken_links': [],
            'rsync_struct_ver': RSYNC_DATA_STRUCT_VERSION,
            'rsync_block_size': RSYNC_BLOCK_SIZE}

        # Get old file meta structure or an empty dict if not available
        old_fs_meta_struct = self.get_fs_meta_struct(manifest_path)

        if os.path.isdir(fs_path):
            # If given path is a directory, change cwd to path to backup
            os.chdir(fs_path)
            for root, dirs, files in os.walk(fs_path):
                self.process_file(root, fs_path, files_meta,
                                  old_fs_meta_struct, write_queue)

                # Check if exclude is in filename. If it is, log the file
                # exclusion and continue to the next iteration.
                if self.exclude:
                    files = [name for name in files if
                             self.exclude not in name]
                    if files:
                        LOG.warning(
                            ('Excluding file names matching with: '
                             '{}'.format(self.exclude)))

                for name in files:
                    file_path = os.path.join(root, name)
                    self.process_file(file_path, fs_path,
                                      files_meta, old_fs_meta_struct,
                                      write_queue)
        else:
            self.process_file(fs_path, os.getcwd(), files_meta,
                              old_fs_meta_struct, write_queue)
        if old_fs_meta_struct:
            for rel_path in old_fs_meta_struct['files']:
                if not files_meta['files'].get(rel_path):
                    self.gen_struct_for_deleted_files(
                        files_meta, old_fs_meta_struct, rel_path, write_queue)

        # Flush any compressed buffered data
        flushed_data = self.compressor.flush()
        if flushed_data:
            flushed_data = self.process_backup_data(flushed_data,
                                                    do_compress=False)
            files_meta['meta']['backup_size_compressed'] += len(flushed_data)
            write_queue.put(flushed_data)

        # General metrics to be uploaded to the API and/or media storage
        files_meta['meta']['broken_links_tot'] = len(
            files_meta['broken_links'])
        files_meta['meta']['total_files'] = len(files_meta['files'])
        files_meta['meta']['total_directories'] = len(
            files_meta['directories'])
        files_meta['meta']['rsync_data_struct_ver'] = RSYNC_DATA_STRUCT_VERSION
        LOG.info("Backup session metrics: {0}".format(
            files_meta['meta']))

        # Compress meta data file
        # Write meta data to disk as JSON
        compressed_json_meta = compress.one_shot_compress(
            self.compression_algo, json.dumps(files_meta))
        with open(manifest_path, 'wb') as manifest_file:
            manifest_file.write(compressed_json_meta)

        # Put False on the queue so it will be terminated on the other side:
        write_queue.put(False)

    def get_fs_meta_struct(self, fs_meta_path):
        fs_meta_struct = {}

        if os.path.isfile(fs_meta_path):
            with open(fs_meta_path) as meta_file:
                fs_meta_struct = json.loads(
                    compress.one_shot_decompress(self.compression_algo,
                                                 meta_file.read()))

        return fs_meta_struct

    @staticmethod
    def is_reg_file(file_type):
        if file_type in REG_FILE:
            return True
        return False

    @staticmethod
    def get_old_file_meta(old_fs_meta_struct, rel_path):
        if old_fs_meta_struct:
            return old_fs_meta_struct['files'].get(rel_path)
        return None

    @staticmethod
    def compute_checksums(rel_path, files_meta, reg_file=True):
        # Files type where the file content can be backed up
        if reg_file:
            with open(rel_path, 'rb') as file_path_fd:
                files_meta['files'][rel_path].update(
                    {'signature': pyrsync.blockchecksums(
                        file_path_fd, RSYNC_BLOCK_SIZE)})
        else:
            # Stat the file to be sure it's not a broken link
            if os.path.lexists(rel_path):
                if not os.path.exists(rel_path):
                    raise IOError

            files_meta['files'][rel_path].update(
                {'signature': [[], []]})

        return files_meta

    def compute_incrementals(
            self, rel_path, inode_str_struct,
            inode_dict_struct, files_meta,
            old_fs_meta_struct, write_queue, deleted=False):

        file_header = self.gen_file_header(
            rel_path, inode_str_struct)

        # File size is header size + null bytes + file size
        file_size = len(file_header)
        reg_file_type = self.is_reg_file(inode_dict_struct['inode']['ftype'])
        try:
            files_meta['files'][rel_path] = inode_dict_struct

            # As pyrsync functions run thorough the file descriptor
            # we need to set the set the pointer to the fd to 0.
            # Backup file data content only if the file type is
            # regular or unknown
            old_file_meta = self.get_old_file_meta(old_fs_meta_struct,
                                                   rel_path)
            if old_file_meta:
                if self.is_file_modified(old_file_meta,
                                         files_meta['files'][rel_path]):
                    # If old_fs_path is provided, it checks
                    # if old file mtime or ctime are different then
                    # the new ones
                    files_meta = self.compute_checksums(rel_path, files_meta,
                                                        reg_file=reg_file_type)

                    compressed_block = self.process_backup_data(file_header)
                    write_queue.put(compressed_block)

                    if reg_file_type:
                        file_path_fd = open(rel_path)
                        for data_block in self.rsync_gen_delta(
                                file_path_fd, old_file_meta):

                            compressed_block = self.process_backup_data(
                                data_block)
                            write_queue.put(compressed_block)
                        file_path_fd.close()
                else:
                    files_meta['files'][rel_path].update(
                        {'signature': old_file_meta['signature']})

            else:
                files_meta = self.compute_checksums(
                    rel_path, files_meta,
                    reg_file=reg_file_type)

                compressed_block = self.process_backup_data(file_header)
                write_queue.put(compressed_block)
                if reg_file_type:
                    file_path_fd = open(rel_path)
                    data_block = file_path_fd.read(
                        RSYNC_BLOCK_BUFF_SIZE)
                    while data_block:
                        compressed_block = self.process_backup_data(data_block)
                        write_queue.put(compressed_block)
                        data_block = file_path_fd.read(
                            RSYNC_BLOCK_BUFF_SIZE)

                    file_path_fd.close()
            files_meta['files'][rel_path]['file_data_len'] = file_size
        except (IOError, OSError) as error:
            LOG.warning('IO or OS Error: {}'.format(error))
            if os.path.lexists(rel_path):
                LOG.warning(
                    'Broken link at: {}'.format(rel_path))
                files_meta['broken_links'].append(rel_path)

        return files_meta
