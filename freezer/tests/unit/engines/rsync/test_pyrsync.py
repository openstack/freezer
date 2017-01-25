# (C) Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import six

from freezer.engine.rsync import pyrsync


class TestPyrsync(unittest.TestCase):
    def test_blockcheksum(self):
        instream = six.BytesIO(b'aae9dd83aa45f906'
                               b'a4629f42e97eac99'
                               b'b9882284dc7030ca'
                               b'427ad365fedd2a55')
        weak, strong = pyrsync.blockchecksums(instream, 16)
        exp_weak = [736756931, 616825970, 577963056, 633341072]
        exp_strong = ['0f923c37c14f648de4065d4666c2429231a923bc',
                      '9f043572d40922cc45545bd6ec8a650ca095ab84',
                      '3a0c39d59a6f49975c2be24bc6b37d80a6680dce',
                      '81487d7e87190cfbbf4f74acc40094c0a6f6ce8a']
        self.assertEqual((weak, strong), (exp_weak, exp_strong))

    def test_rsyncdelta(self):
        datastream = six.BytesIO(b'addc830058f917ae'
                                 b'a1be5ab4d899b570'
                                 b'85c9534c64d8d71c'
                                 b'1f32cde9c71e5b6d')

        old_weak = [675087508, 698025105, 579470394, 667092162]
        old_strong = ['e72251cb70a1b918ee43876896ebb4c8a7225f78',
                      '3bf6d2483425e8925df06c01ee490e386a9a707a',
                      '0ba97d95cc49b1ee2863b7dec3d49911502111c2',
                      '8b92d9f3f6679e1c8ce2f20e2a6217fd7f351f8f']

        changed_indexes = []
        cur_index = 0
        for block_index in pyrsync.rsyncdelta(datastream,
                                              (old_weak, old_strong), 16):
            if not isinstance(block_index, int):
                changed_indexes.append(cur_index)
            cur_index += 1
        exp_changed_indexes = [0, 2]
        self.assertEqual(changed_indexes[:-1], exp_changed_indexes)
