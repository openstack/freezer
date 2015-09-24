#!/usr/bin/env python

from freezer.arguments import alter_proxy
import os
import pytest


class TestArguments(object):

    def prepare_env(self):
        os.environ["HTTP_PROXY"] = 'http://proxy.original.domain:8080'
        os.environ.pop("HTTPS_PROXY", None)

    def test_alter_proxy(self):
        """
        Testing freezer.arguments.alter_proxy function does it set
        HTTP_PROXY and HTTPS_PROXY when 'proxy' key in its dictionary
        """
        # Test wrong proxy value
        test_dict = {'proxy', 'boohoo'}
        with pytest.raises(Exception):
            alter_proxy(test_dict)

        # Test when 'proxy' key has no value
        self.prepare_env()
        test_dict = {'proxy' : ''}
        alter_proxy(test_dict)
        assert "HTTP_PROXY" not in os.environ
        assert "HTTPS_PROXY" not in os.environ

        # Test when there is proxy value passed
        self.prepare_env()
        test_proxy = 'http://proxy.alternative.domain:8888'
        test_dict = {'proxy' : test_proxy}
        alter_proxy(test_dict)
        assert os.environ["HTTP_PROXY"] == test_proxy
        assert os.environ["HTTPS_PROXY"] == test_proxy
