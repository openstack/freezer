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


import logging
import os
import re

from six.moves import configparser
from six.moves import cStringIO

from freezer.utils import utils


class Config:

    @staticmethod
    def parse(config_path):
        if config_path:
            if not os.path.exists(config_path):
                logging.error("[*] Critical Error: Configuration file {0} not"
                              " found".format(config_path))
                raise Exception("Configuration file {0} not found !".format(
                    config_path))
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


EXPORT = re.compile(r"^\s*export\s+([^=^#^\s]+)\s*=\s*([^#^\n]*)\s*$",
                    re.MULTILINE)

INI = re.compile(r"^\s*([^=#\s]+)\s*=[\t]*([^#\n]*)\s*$", re.MULTILINE)

def osrc_parse(lines):
    """
    :param lines:
    :type lines: str
    :return:
    """
    return find_all(EXPORT, lines)

def ini_parse(lines):
    """
    :param lines:
    :type lines: str
    :return:
    """
    try:
        fd = cStringIO.StringIO(lines)
        parser = configparser.ConfigParser()
        parser.readfp(fd)
        return dict(parser.items('default'))
    except Exception as e:
        try:
            # TODO: Remove the parsing of ini-like file via regex
            conf = find_all(INI, lines)
            logging.warning("Using non-INI files for database configuration "
                            "file is deprecated. Falling back to Regex.")
            logging.warning("INI parser error was: {}".format(str(e)))
            return conf
        except Exception:
            logging.warning("Couldn't parse non-INI config file using Regex")
            raise

def find_all(regex, lines):
    return dict([(k.strip(), utils.dequote(v.strip())) for k, v in
                 regex.findall(lines)])
