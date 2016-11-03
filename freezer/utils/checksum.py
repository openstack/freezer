# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib
import os

import six
from six import moves

from freezer.utils import utils


class CheckSum(object):
    """
    Checksum a file or directory with sha256 or md5 algorithms.

    This is used by backup and restore jobs to check for backup consistency.

    - **parameters**::
        :param path: the path to the file or directory to checksum
        :type path: string
        :param hasher_type: the hashing algorithm to use for checksum
        :type hasher_type: string
        :param hasher: hasher object for the specified hasher_type
        :type hasher: hashlib object
        :param blocksize: the max. size of block to read when hashing a file
        :type blocksize: integer
        :param exclude: pattern of files to exclude
        :type exclude: string
        :param checksum: final result for checksum computing
        :type checksum: string
        :param real_checksum: checksum without filename appended if unique file
        :type real_checksum: string
        :param count: number of files checksummed
        :type count: int
    """
    hashes = []

    def __init__(self, path, hasher_type='sha256', blocksize=1048576,
                 exclude='', ignorelinks=False):
        """
        Just variables initialization
        """
        self.path = path
        self.set_hasher(hasher_type)
        self.blocksize = blocksize
        self.exclude = exclude
        self._increment_hash = ''
        self.count = 0
        self.ignorelinks = ignorelinks

    def set_hasher(self, hasher_type):
        """
        Sets the hasher from hashlib according to the chosen hasher_type.
        Also sets the size of the expected output
        """
        if hasher_type == 'sha256':
            self.hasher = hashlib.sha256()
            self.hasher_size = 64
        elif hasher_type == 'md5':
            self.hasher = hashlib.md5()
            self.hasher_size = 32
        else:
            raise ValueError(
                "Unknown hasher_type for checksum: {}".format(hasher_type))

    def get_files_hashes_in_path(self):
        """
        Walk the files in path computing the checksum for each one and updates
        the concatenation checksum for the final result
        """
        self.count = utils.walk_path(self.path, self.exclude,
                                     self.ignorelinks, self.get_hash)

        return self._increment_hash

    def get_hash(self, filepath):
        """
        Open filename and calculate its hash.
        Append the hash to the previous result and stores the checksum for
        this concatenation
        :param filepath: path to file
        :type filepath: string
        :return: string containing the hash of the given file
        """
        if (os.path.isfile(filepath) and not (
                os.path.islink(filepath) and self.ignorelinks)):
            file_hash = self.hashfile(open(filepath, 'rb'))
        else:
            file_hash = self.hashstring(filepath)
        if not self._increment_hash:
            self._increment_hash = file_hash
        else:
            self._increment_hash = self.hashstring(
                self._increment_hash + file_hash)
        return file_hash

    def hashfile(self, afile):
        """
        Checksum a single file with the chosen algorithm.
        The file is read in chunks of self.blocksize.
        :return: string
        """
        # encode_buffer = False

        buf = afile.read(self.blocksize)
        while buf:
            # Need to use string-escape for Python 2 non-unicode strings. For
            # Python 2 unicode strings and all Python 3 strings, we need to use
            # unicode-escape. The effect of them is the same.
            if six.PY2 and isinstance(buf, str):
                buf = buf.encode('string-escape')
            else:
                buf = buf.encode('unicode-escape')

            self.hasher.update(buf)
            buf = afile.read(self.blocksize)
        return self.hasher.hexdigest()

    def hashstring(self, string):
        """
        :return: the hash for a given string
        """
        fd = moves.StringIO(string)
        return self.hashfile(fd)

    def compute(self):
        """
        Compute the checksum for the given path.
        If a single file is provided, the result is its checksum concatenated
        with its name.
        If a directory is provided, the result is the checksum of the checksum
        concatenation for each file.
        :return: string
        """
        self.checksum = self.get_files_hashes_in_path()
        self.real_checksum = self.checksum
        # This appends the filename when checksum was made for a single file.
        # We need to get this when testing the consistency on the moment of
        # restore.
        if self.count == 1:
            self.checksum = self.real_checksum + os.path.basename(self.path)
        return self.checksum

    def compare(self, checksum):
        """
        Compute the checksum for the object path and compare with the given
        checksum.
        :return: boolean
        """
        real_checksum = checksum
        if len(checksum) > self.hasher_size:
            real_checksum = checksum[0:self.hasher_size]
            afile = checksum[self.hasher_size:len(checksum)]
            self.path = os.path.join(self.path, afile)
        self.compute()
        return self.real_checksum == real_checksum
