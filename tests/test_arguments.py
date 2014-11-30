#!/usr/bin/env python

from freezer.arguments import  backup_arguments
import argparse
from commons import *
import sys
import pytest
import distutils.spawn as distspawn
import __builtin__


class TestArguments:

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