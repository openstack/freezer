# (C) Copyright 2016 Mirantis, Inc.
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

GZIP = 'zlib'
BZIP2 = 'bz2'
XZ = 'lzma'

COMPRESS_METHOD = 'compress'
DECOMPRESS_METHOD = 'decompress'


def get_compression_algo(compression_algo):
    algo = {
        'gzip': GZIP,
        'bzip2': BZIP2,
        'xz': XZ,
    }
    return algo.get(compression_algo)


def one_shot_compress(compression_algo, data):
    compression_module = __import__(get_compression_algo(compression_algo))
    return getattr(compression_module, COMPRESS_METHOD)(data)


def one_shot_decompress(compression_algo, data):
    compression_module = __import__(get_compression_algo(compression_algo))
    return getattr(compression_module, DECOMPRESS_METHOD)(data)


class BaseCompressor(object):
    """
    Base class for compress/decompress activities.
    """

    def __init__(self, compression_algo):
        # TODO(raliev): lzma module exists in stdlib since Py3 only
        if compression_algo == 'xz':
            raise NotImplementedError('XZ compression not implemented yet')
        self.algo = get_compression_algo(compression_algo)
        self.module = __import__(self.algo)


class Compressor(BaseCompressor):
    """
    Compress chucks of data.
    """

    MAX_COMPRESS_LEVEL = 9

    def __init__(self, compression_algo):
        super(Compressor, self).__init__(compression_algo)
        self.compressobj = self.create_compressobj(compression_algo)

    def create_compressobj(self, compression_algo):
        def get_obj_name():
            names = {
                'gzip': 'compressobj',
                'bzip2': 'BZ2Compressor',
                'xz': 'compressobj',
            }
            return names.get(compression_algo)

        obj_name = get_obj_name()
        return getattr(self.module, obj_name)(self.MAX_COMPRESS_LEVEL)

    def compress(self, data):
        return self.compressobj.compress(data)

    def flush(self):
        return self.compressobj.flush()


class Decompressor(BaseCompressor):
    """
    Decompress chucks of data.
    """

    def __init__(self, compression_algo):
        super(Decompressor, self).__init__(compression_algo)
        self.decompressobj = self.create_decompressobj(compression_algo)

    def create_decompressobj(self, compression_algo):
        def get_obj_name():
            names = {
                'gzip': 'decompressobj',
                'bzip2': 'BZ2Decompressor',
                'xz': 'decompressobj',
            }
            return names.get(compression_algo)

        obj_name = get_obj_name()
        return getattr(self.module, obj_name)()

    def decompress(self, data):
        return self.decompressobj.decompress(data)

    def flush(self):
        return self.decompressobj.flush()
