"""Freezer Setup Python file.
"""
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import os

here = os.path.abspath(os.path.dirname(__file__))


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        import sys
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


setup(
    name='freezer',
    version='1.1.0',
    url='https://github.com/stackforge/freezer',
    license='Apache Software License',
    author='Fausto Marzi, Ryszard Chojnacki, Emil Dimitrov',
    author_email='fausto.marzi@hp.com, ryszard@hp.com, edimitrov@hp.com',
    maintainer='Fausto Marzi, Ryszard Chojnacki, Emil Dimitrov',
    maintainer_email='fausto.marzi@hp.com, ryszard@hp.com, edimitrov@hp.com',
    tests_require=['pytest'],
    description=('OpenStack incremental backup and restore automation tool '
                 'for file system, MongoDB, MySQL. LVM snapshot and '
                 'encryption support'),
    long_description=open('README.rst').read(),
    keywords="OpenStack Swift backup restore mongodb mysql lvm snapshot",
    packages=find_packages(),
    platforms='Linux, *BSD, OSX',
    cmdclass={'test': PyTest},
    scripts=['bin/freezerc'],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Environment :: OpenStack',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: BSD :: NetBSD',
        'Operating System :: POSIX :: BSD :: OpenBSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Compression',
        'Topic :: System :: Archiving',
    ],
    install_requires=[
        'python-swiftclient>=1.6.0',
        'python-keystoneclient>=0.7.0',
        'mysql-python',
        'pymongo',
        'docutils>=0.8.1'],
    extras_require={
        'testing': ['pytest', 'flake8'],
    }
)
