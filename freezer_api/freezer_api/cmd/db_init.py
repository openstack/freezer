#!/usr/bin/env python2
"""
Copyright 2015 Hewlett-Packard

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
"""

import argparse
import os
import json
import re
import requests
import sys
import ConfigParser

from freezer_api.common import db_mappings


DEFAULT_CONF_PATH = '/etc/freezer-api.conf'
DEFAULT_ES_SERVER_PORT = 9200
DEFAULT_INDEX = 'freezer'


class ElastichsearchEngine(object):
    def __init__(self, es_url, es_index, test_only, always_yes, verbose):
        self.es_url = es_url
        self.es_index = es_index
        self.test_only = test_only
        self.always_yes = always_yes
        self.verbose = verbose

    def verbose_print(self, message):
        if self.verbose:
            print(message)

    def put_mappings(self, mappings):
        self.check_index_exists()
        for es_type, mapping in mappings.iteritems():
            if self.mapping_match(es_type, mapping):
                print '{0}/{1} MATCHES'.format(self.es_index, es_type)
            else:
                self.askput_mapping(es_type, mapping)

    def check_index_exists(self):
        url = '{0}/{1}'.format(self.es_url, self.es_index)
        r = requests.post(url)
        if r.status_code not in [requests.codes.OK,
                                 requests.codes.BAD_REQUEST]:
            raise Exception('Unable to check/create index {0}. '
                            'ERROR {1}'.format(url, r.status_code))

    def mapping_match(self, es_type, mapping):
        url = '{0}/{1}/_mapping/{2}'.format(self.es_url,
                                            self.es_index,
                                            es_type)
        self.verbose_print("Getting mappings: http GET {0}".format(url))
        r = requests.get(url)
        self.verbose_print("response: {0}".format(r))
        if r.status_code == requests.codes.NOT_FOUND:
            return False
        if r.status_code != requests.codes.OK:
            raise Exception("ERROR {0}: {1}".format(r.status_code, r.text))
        current_mappings = r.json().get(self.es_index, {}).get('mappings', {})
        return mapping == current_mappings.get(es_type, {})

    def askput_mapping(self, es_type, mapping):
        if self.test_only:
            print '{0}/{1} DOES NOT MATCH'.format(self.es_index, es_type)
            return
        prompt_message = ('{0}/{1}/{2} needs to be deleted. '
                          'Proceed (y/n) ? '.format(self.es_url,
                                                    self.es_index,
                                                    es_type))
        if self.always_yes or self.proceed(prompt_message):
            self.delete_type(es_type)
            self.put_mapping(es_type, mapping)

    def delete_type(self, es_type):
        url = '{0}/{1}/{2}'.format(self.es_url, self.es_index, es_type)
        self.verbose_print("DELETE {0}".format(url))
        r = requests.delete(url)
        self.verbose_print("response: {0}".format(r))
        if r.status_code not in [requests.codes.OK, requests.codes.NOT_FOUND]:
            raise Exception('Type removal error {0}: '
                            '{1}'.format(r.status_code, r.text))

    def put_mapping(self, es_type, mapping):
        url = '{0}/{1}/_mapping/{2}'.format(self.es_url,
                                            self.es_index,
                                            es_type)
        self.verbose_print('PUT {0}'.format(url))
        r = requests.put(url, data=json.dumps(mapping))
        self.verbose_print("response: {0}".format(r))
        if r.status_code == requests.codes.OK:
            print "Type {0} mapping created".format(url)
        else:
            raise Exception('Type mapping creation error {0}: '
                            '{1}'.format(r.status_code, r.text))

    def proceed(self, message):
        if self.always_yes:
            return True
        while True:
            selection = raw_input(message)
            if selection.upper() == 'Y':
                return True
            elif selection.upper() == 'N':
                return False


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        'host', action='store', default='', nargs='?',
        help='The DB host address[:port], default "localhost"')
    arg_parser.add_argument(
        '-p', '--port', action='store', type=int,
        help=('The DB server port '
              '(default: {0})'.format(DEFAULT_ES_SERVER_PORT)),
        dest='port', default=0)
    arg_parser.add_argument(
        '-i', '--index', action='store',
        help='The DB index (default "{0}")'.format(DEFAULT_INDEX),
        dest='index')
    arg_parser.add_argument(
        '-y',  '--yes', action='store_true',
        help="Automatic confirmation to index removal",
        dest='yes', default=False)
    arg_parser.add_argument(
        '-v',  '--verbose', action='store_true',
        help="Verbose",
        dest='verbose', default=False)
    arg_parser.add_argument(
        '-t',  '--test-only', action='store_true',
        help="Test the validity of the mappings, but take no action",
        dest='test_only', default=False)
    arg_parser.add_argument(
        '-c', '--config-file', action='store',
        help='Config file with the db information',
        dest='config_file', default='')

    return arg_parser.parse_args()


def find_config_file():
    cwd_config = os.path.join(os.getcwd(), 'freezer-api.conf')
    for config_file_path in [cwd_config, DEFAULT_CONF_PATH]:
        if os.path.isfile(config_file_path):
            return config_file_path


def parse_config_file(fname):
    """
    Read host URL from config-file

    :param fname: config-file path
    :return: (host, port, db_index)
    """
    if not fname:
        return None, 0, None

    host, port, index = None, 0, None

    config = ConfigParser.ConfigParser()
    config.read(fname)
    try:
        endpoint = config.get('storage', 'endpoint')
        match = re.search(r'^http://([^:]+):([\d]+)$', endpoint)
        if match:
            host = match.group(1)
            port = int(match.group(2))
    except:
        pass
    try:
        index = config.get('storage', 'index')
    except:
        pass
    return host, int(port), index


def get_db_params(args):
    """
    Extracts the db configuration parameters either from the provided
    command line arguments or searching in the default freezer-api config
    file /etc/freezer-api.conf

    :param args: argparsed command line arguments
    :return: (elasticsearch_url, elastichsearch_index)
    """
    conf_fname = args.config_file or find_config_file()

    if args.verbose:
        print "using config file: {0}".format(conf_fname)

    conf_host, conf_port, conf_db_index = parse_config_file(conf_fname)

    # host lookup
    #   1) host arg (before ':')
    #   2) config file provided
    #   3) string 'localhost'
    host = args.host or conf_host or 'localhost'
    host = host.split(':')[0]

    # port lookup
    #   1) port arg
    #   2) host arg (after ':')
    #   3) config file provided
    #   4) DEFAULT_ES_SERVER_PORT
    match_port = None
    match = re.search(r':(\d+)$', args.host)
    if match:
        match_port = match.groups()[0]

    port = args.port or match_port or conf_port or DEFAULT_ES_SERVER_PORT

    elasticsearch_url = 'http://{0}:{1}'.format(host, port)

    # index lookup
    # 1) index args
    # 2) config file
    # 3) string DEFAULT_INDEX
    elasticsearch_index = args.index or conf_db_index or DEFAULT_INDEX

    return elasticsearch_url, elasticsearch_index


def main():
    args = get_args()

    elasticsearch_url, elasticsearch_index = get_db_params(args)

    es_manager = ElastichsearchEngine(es_url=elasticsearch_url,
                                      es_index=elasticsearch_index,
                                      test_only=args.test_only,
                                      always_yes=args.yes,
                                      verbose=args.verbose)

    if args.verbose:
        print "  db url: {0}".format(elasticsearch_url)
        print "db index: {0}".format(elasticsearch_index)

    mappings = db_mappings.get_mappings()

    try:
        es_manager.put_mappings(mappings)
    except Exception as e:
        print "ERROR {0}".format(e)
        return os.EX_DATAERR

    return os.EX_OK

if __name__ == '__main__':
    sys.exit(main())
