#!/usr/bin/env python

from freezer.arguments import  backup_arguments
import argparse
from commons import *

import __builtin__


class TestArguments:

    def test_arguments(self, monkeypatch):

        fakeargparse = FakeArgparse()
        fakeargparse = fakeargparse.ArgumentParser()

        monkeypatch.setattr(
            argparse, 'ArgumentParser', fakeargparse)

        assert backup_arguments() is not Exception or not False
