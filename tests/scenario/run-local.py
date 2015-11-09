#!/usr/bin/python

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

"""

import os
import sys
import logging
from unittest import TestLoader, TextTestRunner, TestSuite
from backup_scenario import BackupScenarioFS

SWIFT_CONF = 'swiftrc'

def load_swift_env(fname):
    file_lines = open(fname, 'r').readlines()
    for line in file_lines:
        if ' ' not in line.strip():
            continue
        (cmd, line) = line.split()
        if cmd.strip().lower() == 'unset':
            os.environ.pop(line, None)
        elif '=' in line.strip():
            (key, val) = line.split('=')
            os.environ[key.strip()] = val.strip()

if __name__ == "__main__":
    load_swift_env(SWIFT_CONF)
    logging.disable(logging.CRITICAL)
    os.system('./vagrant-scripts/create-lvm.sh 1')
    loader = TestLoader()
    suite = TestSuite(
        loader.loadTestsFromTestCase(BackupScenarioFS),
        )
    runner = TextTestRunner(verbosity = 2)
    runner.run(suite)
