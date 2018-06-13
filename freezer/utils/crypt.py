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

import hashlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes
from os import urandom

SALT_HEADER = 'Salted__'
AES256_KEY_LENGTH = 32
BS = 16  # static 16 bytes, 128 bits for AES


class AESCipher(object):
    """
    Base class for encrypt/decrypt activities.
    """

    def __init__(self, pass_file):
        self._password = self._get_pass_from_file(pass_file)
        self._salt = None
        self.cipher = None

    @staticmethod
    def _get_pass_from_file(pass_file):
        with open(pass_file) as p_file:
            password = p_file.readline()
        return password

    @staticmethod
    def _derive_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = b''
        while len(d) < key_length + iv_length:
            md5_str = d_i + password + salt
            d_i = hashlib.md5(md5_str).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length + iv_length]


class AESEncrypt(AESCipher):
    """
    Encrypts chucks of data using AES-256 algorithm.
    OpenSSL compatible.
    """

    def __init__(self, pass_file):
        super(AESEncrypt, self).__init__(pass_file)
        self._salt = urandom(BS - len(SALT_HEADER))
        key, iv = self._derive_key_and_iv(self._password,
                                          self._salt,
                                          AES256_KEY_LENGTH,
                                          BS)
        self.cipher = Cipher(algorithms.AES(key),
                             modes.CFB(iv),
                             backend=default_backend())

    def generate_header(self):
        return SALT_HEADER + self._salt

    def encrypt(self, data):
        encryptor = self.cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()


class AESDecrypt(AESCipher):
    """
    Decrypts chucks of data using AES-256 algorithm.
    OpenSSL compatible.
    """

    def __init__(self, pass_file, salt):
        super(AESDecrypt, self).__init__(pass_file)
        self._salt = self._prepare_salt(salt)
        key, iv = self._derive_key_and_iv(self._password,
                                          self._salt,
                                          AES256_KEY_LENGTH,
                                          BS)
        self.cipher = Cipher(algorithms.AES(key),
                             modes.CFB(iv),
                             backend=default_backend())

    @staticmethod
    def _prepare_salt(salt):
        return salt[len(SALT_HEADER):]

    def decrypt(self, data):
        decryptor = self.cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()
