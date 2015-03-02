#!/usr/bin/env python

from freezer.arguments import  backup_arguments, alter_proxy
import argparse
from commons import *
import sys
import os
import pytest
import distutils.spawn as distspawn
import __builtin__


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

    def test_arguments(self, monkeypatch):
        fakeargparse = FakeArgparse()
        fakeargparse = fakeargparse.ArgumentParser()
        fakedistutils = FakeDistutils()
        fakedistutilsspawn = fakedistutils.spawn()

        monkeypatch.setattr(
            argparse, 'ArgumentParser', fakeargparse)

        platform = sys.platform
        assert backup_arguments() is not False

        sys.__dict__['platform'] = 'darwin'
        pytest.raises(Exception, backup_arguments)
        monkeypatch.setattr(
            distspawn, 'find_executable', fakedistutilsspawn.find_executable)
        assert backup_arguments() is not False
        sys.__dict__['platform'] = platform
