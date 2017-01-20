"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This is a pure Python implementation of the [rsync algorithm] [TM96].
Updated to use SHA256 hashing (instead of the standard implementation
which uses outdated MD5 hashes), and packages for disutils
distribution by Isis Lovecruft, <isis@patternsinthevoid.net>. The
majority of the code is blatantly stolen from Eric Pruitt's code
as posted on [ActiveState] [1].
[1]: https://code.activestate.com/recipes/577518-rsync-algorithm/
[TM96]: Andrew Tridgell and Paul Mackerras. The rsync algorithm.
Technical Report TR-CS-96-05, Canberra 0200 ACT, Australia, 1996.
http://samba.anu.edu.au/rsync/.

"""

import collections
import hashlib

import six
from six.moves import range


if six.PY2:
    # Python 2.x compatibility
    def bytes(var, *args):
        try:
            return ''.join(map(chr, var))
        except TypeError:
            return map(ord, var)

__all__ = ["rollingchecksum", "weakchecksum", "rsyncdelta",
           "blockchecksums"]


def rollingchecksum(removed, new, a, b, blocksize=4096):
    """
    Generates a new weak checksum when supplied with the internal state
    of the checksum calculation for the previous window, the removed
    byte, and the added byte.
    """
    a -= removed - new
    b -= removed * blocksize - a
    return (b << 16) | a, a, b


def weakchecksum(data):
    """
    Generates a weak checksum from an iterable set of bytes.
    """
    a = b = 0
    l = len(data)
    for i in range(l):
        a += data[i]
        b += (l - i) * data[i]

    return (b << 16) | a, a, b


def blockchecksums(instream, blocksize=4096):
    """
    Returns a list of weak and strong hashes for each block of the
    defined size for the given data stream.
    """

    weakhashes = list()
    stronghashes = list()
    read = instream.read(blocksize)

    while read:
        weakhashes.append(weakchecksum(bytes(read))[0])
        stronghashes.append(hashlib.sha1(read).hexdigest())
        read = instream.read(blocksize)

    return weakhashes, stronghashes


def rsyncdelta(datastream, remotesignatures, blocksize=4096):
    """
    Generates a binary patch when supplied with the weak and strong
    hashes from an unpatched target and a readable stream for the
    up-to-date data. The blocksize must be the same as the value
    used to generate remotesignatures.
    """

    remote_weak, remote_strong = remotesignatures

    match = True
    matchblock = -1
    last_byte = []
    while True:
        if match and datastream is not None:
            # Whenever there is a match or the loop is running for the first
            # time, populate the window using weakchecksum instead of rolling
            # through every single byte which takes at least twice as long.
            window = collections.deque(bytes(datastream.read(blocksize)))
            checksum, a, b = weakchecksum(window)

        try:
            # If there are two identical weak checksums in a file, and the
            # matching strong hash does not occur at the first match, it will
            # be missed and the data sent over. May fix eventually, but this
            # problem arises very rarely.
            matchblock = remote_weak.index(checksum, matchblock + 1)
            stronghash = hashlib.sha1(bytes(window)).hexdigest()
            matchblock = remote_strong.index(stronghash, matchblock)

            match = True
            # print "MATCHBLOCK: {}".format(matchblock)
            # print "MATCHBLOCK TYPE: {}".format(type(matchblock))
            # print "LAST BYTE WHEN MATCH: {}".format(last_byte)
            if last_byte:
                yield bytes(last_byte)
                last_byte = []
            yield matchblock
            if datastream.closed:
                break
            continue

        except ValueError:
            # The weakchecksum did not match
            match = False
            try:
                if datastream:
                    # Get the next byte and affix to the window
                    newbyte = ord(datastream.read(1))
                    window.append(newbyte)
            except TypeError:
                # No more data from the file; the window will slowly shrink.
                # newbyte needs to be zero from here on to keep the checksum
                # correct.
                newbyte = 0
                tailsize = datastream.tell() % blocksize
                datastream = None

            if datastream is None and len(window) <= tailsize:
                # The likelihood that any blocks will match after this is
                # nearly nil so call it quits.
                yield bytes(window)
                break

            # Yank off the extra byte and calculate the new window checksum
            oldbyte = window.popleft()
            checksum, a, b = rollingchecksum(oldbyte, newbyte, a, b, blocksize)

            last_byte.append(oldbyte)
            if len(last_byte) == blocksize:
                yield bytes(last_byte)
                last_byte = []
