#!/usr/bin/env python

from freezer.backup import (
    backup_mode_mysql, backup_mode_fs, backup_mode_mongo)
from freezer.arguments import backup_arguments

import time
import os


def test_backup_mode_mysql():

    # THE WHOLE TEST NEED TO BE CHANGED USING MOCK!!
    # Return backup options and arguments
    backup_args = backup_arguments()

