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


import hashlib
import zlib


_BASE = 65521  # largest prime smaller than 65536


def adler32fast(data):
    return zlib.adler32(data) & 0xffffffff


def adler32(data):
    checksum = zlib.adler32(data)
    s2, s1 = (checksum >> 16) & 0xffff, checksum & 0xffff
    return checksum & 0xffffffff, s1, s2


def adler32rolling(removed, new, s1, s2, blocksize=4096):
    r = ord(removed)
    n = ord(new)
    s1 = (s1 + n - r) % _BASE
    s2 = (s2 + s1 - blocksize * r - 1) % _BASE
    return ((s2 << 16) | s1) & 0xffffffff, s1, s2


def blockchecksums(args):
    """
    Returns a list of weak and strong hashes for each block of the
    defined size for the given data stream.
    """
    path, blocksize = args
    weakhashes = []
    stronghashes = []
    weak_append = weakhashes.append
    strong_append = stronghashes.append

    with open(path, 'rb') as instream:
        instream_read = instream.read
        read = instream_read(blocksize)

        while read:
            weak_append(adler32fast(read))
            strong_append(hashlib.sha1(read).hexdigest())
            read = instream_read(blocksize)

    return weakhashes, stronghashes


def rsyncdelta_fast(datastream, remotesignatures, blocksize=4096):
    rem_weak, rem_strong = remotesignatures
    data_block = datastream.read(blocksize)
    index = 0
    while data_block:
        try:
            if adler32fast(data_block) == rem_weak[index] and hashlib.sha1(
                    data_block).hexdigest() == rem_strong[index]:
                yield index
            else:
                yield data_block
        except IndexError:
            yield data_block

        index += 1
        data_block = datastream.read(blocksize)
