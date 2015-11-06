#(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

from setuptools import setup
import sys
import subprocess

# All this Machinery unfortunately is needed to support win32 platform.
# We follow the advice from pbr as:
# Note that we do nott support the easy_install aspects of setuptools:
# while we depend on setup_requires, for any install_requires we recommend
# that they be installed prior to running setup.py install - either by hand,
# or by using an install tool such as pip.
install_requires = ''
if sys.platform.startswith('linux'):
    install_requires = 'pep3143daemon'
elif sys.platform.startswith('win32'):
    install_requires = 'pywin32'

subprocess.call(['easy_install', 'pip'])
if install_requires:
  subprocess.call(['pip', 'install', install_requires])

setup(
    setup_requires='pbr>=0.6,!=0.7,<1.0',
    pbr=True
)

