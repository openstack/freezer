#!/usr/bin/env python

from freezer.arguments import backup_arguments
import pytest
import argparse

def test_backup_arguments():

    backup_args, arg_parser = backup_arguments()
    assert backup_args.tar_path is not False
    assert backup_args.mode is ('fs' or 'mysql' or 'mongo')
