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

# import errno
# import ftplib
# import os
# import shutil
# import socket
# import tempfile
from oslo_log import log

from freezer.storage import fslike
# from freezer.utils import utils

CHUNK_SIZE = 32768
LOG = log.getLogger(__name__)


class FtpsStorage(fslike.FsLikeStorage):
    """
    :type ftps: paramiko.SFTPClient
    """
    _type = 'ftps'

    def __init__(self, storage_path, remote_pwd,
                 remote_username, remote_ip, port, max_segment_size):
        pass
