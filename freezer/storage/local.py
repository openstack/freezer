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

"""

import io
import os
import shutil

from freezer.storage import fslike
from freezer.utils import utils


class LocalStorage(fslike.FsLikeStorage):
    _type = 'local'

    def get_file(self, from_path, to_path):
        shutil.copyfile(from_path, to_path)

    def put_file(self, from_path, to_path):
        shutil.copyfile(from_path, to_path)

    def listdir(self, directory):
        try:
            return os.listdir(directory)
        except OSError:
            return list()

    def create_dirs(self, path):
        utils.create_dir_tree(path)

    def rmtree(self, path):
        shutil.rmtree(path)

    def open(self, filename, mode):
        return io.open(filename, mode)
