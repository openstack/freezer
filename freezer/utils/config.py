# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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

import os
import re

from oslo_log import log
import six
from six.moves import configparser

from freezer.utils import utils

LOG = log.getLogger(__name__)


EXPORT = re.compile(r"^\s*export\s+([^=^#^\s]+)\s*=\s*([^#^\n]*)\s*$",
                    re.MULTILINE)

INI = re.compile(r"^\s*([^=#\s]+)\s*=[\t]*([^#\n]*)\s*$", re.MULTILINE)


class Config(object):

    @staticmethod
    def parse(config_path):
        if config_path:
            if not os.path.exists(config_path):
                LOG.error("Critical Error: Configuration file {0} not"
                          " found".format(config_path))
                raise Exception("Configuration file {0} not found !".format(
                    config_path))
        # SafeConfigParser was deprecated in Python 3.2
        if six.PY3:
            config = configparser.ConfigParser()
        else:
            config = configparser.SafeConfigParser()
        config.read([config_path])
        sections = config.sections()
        storages = []
        default_options = {}
        for section in sections:
            dict = {}
            for option in config.options(section):
                option_value = config.get(section, option)
                if option_value in ('False', 'None'):
                    option_value = False
                dict[option] = option_value
            if section.startswith("storage:"):
                storages.append(dict)
            else:
                default_options.update(dict)
        return Config(default_options, storages)

    def __init__(self, default, storages):
        """
        :param default:
        :type default: dict
        :param storages:
        :type storages: list[dict]
        :return:
        """
        self.default = default
        self.storages = storages


def osrc_parse(lines):
    """
    :param lines:
    :type lines: str
    :return:
    """
    return find_all(EXPORT, lines)


def ini_parse(fd):
    """
    :param fd:
    :type fd: file_descriptor
    :return:
    """
    parser = configparser.ConfigParser()
    parser.readfp(fd)
    return dict(parser.items('default'))


def find_all(regex, lines):
    return dict([(k.strip(), utils.dequote(v.strip())) for k, v in
                 regex.findall(lines)])
