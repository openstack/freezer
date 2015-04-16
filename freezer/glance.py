"""
Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

Freezer functions to interact with OpenStack Swift client and server
"""

import logging
from glanceclient.v1 import client as glclient
from glanceclient.shell import OpenStackImagesShell
from freezer.bandwidth import monkeypatch_socket_bandwidth


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __getattr__(self, item):
        return self.__dict__.get(item)


def glance(backup_opt_dict):
    """
    Creates glance client and attached it ot the dictionary
    :param backup_opt_dict: Dictionary with configuration
    :return: Dictionary with attached glance client
    """

    options = backup_opt_dict.options

    monkeypatch_socket_bandwidth(backup_opt_dict)

    endpoint, token = OpenStackImagesShell()._get_endpoint_and_token(
        Bunch(os_username=options.user_name,
              os_password=options.password,
              os_tenant_name=options.tenant_name,
              os_auth_url=options.auth_url,
              os_region_name=options.region_name,
              force_auth=True))

    backup_opt_dict.glance = glclient.Client(endpoint=endpoint, token=token)
    return backup_opt_dict


class ReSizeStream:
    """
    Iterator/File-like object for changing size of chunk in stream
    """
    def __init__(self, stream, length, chunk_size):
        self.stream = stream
        self.length = length
        self.chunk_size = chunk_size
        self.reminder = ""
        self.transmitted = 0

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def next(self):
        logging.info("Transmitted (%s) of (%s)" % (self.transmitted,
                                                   self.length))
        chunk_size = self.chunk_size
        if len(self.reminder) > chunk_size:
            result = self.reminder[:chunk_size]
            self.reminder = self.reminder[chunk_size:]
            self.transmitted += len(result)
            return result
        else:
            stop = False
            while not stop and len(self.reminder) < chunk_size:
                try:
                    self.reminder += next(self.stream)
                except StopIteration:
                    stop = True
            if stop:
                result = self.reminder
                if len(self.reminder) == 0:
                    raise StopIteration()
                self.reminder = []
                self.transmitted += len(result)
                return result
            else:
                result = self.reminder[:chunk_size]
                self.reminder = self.reminder[chunk_size:]
                self.transmitted += len(result)
                return result

    def read(self, chunk_size):
        self.chunk_size = chunk_size
        return self.next()
