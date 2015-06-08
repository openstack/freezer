# Copyright 2015 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import unittest
from mock import Mock, patch

from freezer.scheduler import arguments


class TestOpenstackOptions(unittest.TestCase):

    def setUp(self):
        self.args = Mock()
        self.args.os_username = 'janedoe'
        self.args.os_tenant_name = 'hertenant'
        self.args.os_auth_url = 'herauthurl'
        self.args.os_password = 'herpassword'
        self.args.os_tenant_id = 'hertenantid'
        self.args.os_region_name = 'herregion'
        self.args.os_endpoint = 'herpublicurl'
        self.empty_args = Mock()
        self.empty_args.os_username = ''
        self.empty_args.os_tenant_name = ''
        self.empty_args.os_auth_url = ''
        self.empty_args.os_password = ''
        self.empty_args.os_tenant_id = ''
        self.empty_args.os_region_name = ''
        self.empty_args.os_endpoint = ''

        self.env_dict = {
            'OS_USERNAME': 'johndoe',
            'OS_TENANT_NAME': 'histenant',
            'OS_AUTH_URL': 'hisauthurl',
            'OS_PASSWORD': 'hispassword',
            'OS_TENANT_ID': 'histenantid',
            'OS_REGION_NAME': 'hisregion',
            'OS_SERVICE_ENDPOINT': 'hispublicurl'
        }

    def test_create_with_args_and_env(self):
        os = arguments.OpenstackOptions(self.args, self.env_dict)
        self.assertIsInstance(os, arguments.OpenstackOptions)

    def test_create_with_empty_args_and_empty_env(self):
        os = arguments.OpenstackOptions(self.empty_args, self.env_dict)
        self.assertIsInstance(os, arguments.OpenstackOptions)

    def test_create_with_args_and_empty_env(self):
        os = arguments.OpenstackOptions(self.args, {})
        self.assertIsInstance(os, arguments.OpenstackOptions)

    def test_create_raises_Exception_when_missing_username(self):
        self.args.os_username = ''
        self.assertRaises(Exception, arguments.OpenstackOptions, self.args, {})

    def test_create_raises_Exception_when_missing_p(self):
        self.args.os_password = ''
        self.assertRaises(Exception, arguments.OpenstackOptions, self.args, {})

    def test_create_raises_Exception_when_missing_parameter(self):
        self.args.os_username = ''
        self.assertRaises(Exception, arguments.OpenstackOptions, self.args, {})

    def test_str(self):
        os = arguments.OpenstackOptions(self.args, self.env_dict)
        s = str(os)
        self.assertIsInstance(s, str)


class TestGetArgs(unittest.TestCase):

    @patch('freezer.scheduler.arguments.argparse.ArgumentParser')
    def test_get_args_calls_add_argument(self, mock_ArgumentParser):
        mock_arg_parser = Mock()
        mock_ArgumentParser.return_value = mock_arg_parser

        retval = arguments.get_args(['alpha', 'bravo'])
        call_count = mock_arg_parser.add_argument.call_count
        self.assertGreater(call_count, 15)
