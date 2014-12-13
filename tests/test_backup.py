#!/usr/bin/env python

from freezer.backup import backup_mode_mysql, backup_mode_fs, backup_mode_mongo
import freezer
import swiftclient
import multiprocessing
import subprocess
import time
import os
import MySQLdb
import pymongo
import re
import pytest
from commons import *

import __builtin__


class TestBackUP:

    def test_backup_mode_mysql(self, monkeypatch):

        test_meta = dict()
        backup_opt = BackupOpt1()
        fakemysql = FakeMySQLdb()
        expanduser = Os()
        fakere = FakeRe()
        fakeswiftclient = FakeSwiftClient()
        fakelvm = Lvm()
        fakesubprocess = FakeSubProcess()
        fakesubprocesspopen = fakesubprocess.Popen()
        fakemultiprocessing = FakeMultiProcessing()
        fakemultiprocessingqueue = fakemultiprocessing.Queue()
        fakemultiprocessingpipe = fakemultiprocessing.Pipe()
        fakemultiprocessinginit = fakemultiprocessing.__init__()

        monkeypatch.setattr(
            multiprocessing, 'Queue', fakemultiprocessingqueue)
        monkeypatch.setattr(
            multiprocessing, 'Pipe', fakemultiprocessingpipe)
        monkeypatch.setattr(
            multiprocessing, 'Process', fakemultiprocessing.Process)
        monkeypatch.setattr(
            multiprocessing, '__init__', fakemultiprocessinginit)
        #monkeypatch.setattr(__builtin__, 'open', fakeopen.open)
        monkeypatch.setattr(
            subprocess.Popen, 'communicate', fakesubprocesspopen.communicate)
        monkeypatch.setattr(
            freezer.lvm, 'lvm_snap_remove', fakelvm.lvm_snap_remove)
        monkeypatch.setattr(freezer.lvm, 'lvm_eval', fakelvm.lvm_eval)
        monkeypatch.setattr(re, 'search', fakere.search)
        monkeypatch.setattr(MySQLdb, 'connect', fakemysql.connect)
        monkeypatch.setattr(os.path, 'expanduser', expanduser.expanduser)
        monkeypatch.setattr(os.path, 'isdir', expanduser.isdir)
        monkeypatch.setattr(os, 'makedirs', expanduser.makedirs)
        monkeypatch.setattr(os.path, 'exists', expanduser.exists)
        monkeypatch.setattr(swiftclient, 'client', fakeswiftclient.client)

        mysql_conf_file = backup_opt.mysql_conf_file
        backup_opt.__dict__['mysql_conf_file'] = None
        pytest.raises(Exception, backup_mode_mysql, backup_opt, 123456789, test_meta)

        # Generate mysql conf test file
        backup_opt.__dict__['mysql_conf_file'] = mysql_conf_file
        with open(backup_opt.mysql_conf_file, 'w') as mysql_conf_fd:
            mysql_conf_fd.write('host=abcd\nuser=abcd\npassword=abcd\n')
        assert backup_mode_mysql(
            backup_opt, 123456789, test_meta) is None

        fakemysql2 = FakeMySQLdb2()
        monkeypatch.setattr(MySQLdb, 'connect', fakemysql2.connect)
        pytest.raises(Exception, backup_mode_mysql, backup_opt, 123456789, test_meta)
        os.unlink(backup_opt.mysql_conf_file)

    def test_backup_mode_fs(self, monkeypatch):

        # Class and other settings initialization
        test_meta = dict()
        backup_opt = BackupOpt1()
        backup_opt.mode = 'fs'
        expanduser = Os()
        fakere = FakeRe()
        fakeswiftclient = FakeSwiftClient()
        fakelvm = Lvm()
        fakemultiprocessing = FakeMultiProcessing()
        fakemultiprocessingqueue = fakemultiprocessing.Queue()
        fakemultiprocessingpipe = fakemultiprocessing.Pipe()
        fakemultiprocessinginit = fakemultiprocessing.__init__()

        # Monkey patch
        monkeypatch.setattr(
            multiprocessing, 'Queue', fakemultiprocessingqueue)
        monkeypatch.setattr(multiprocessing, 'Pipe', fakemultiprocessingpipe)
        monkeypatch.setattr(
            multiprocessing, 'Process', fakemultiprocessing.Process)
        monkeypatch.setattr(
            multiprocessing, '__init__', fakemultiprocessinginit)
        monkeypatch.setattr(freezer.lvm, 'lvm_eval', fakelvm.lvm_eval)
        monkeypatch.setattr(swiftclient, 'client', fakeswiftclient.client)
        monkeypatch.setattr(re, 'search', fakere.search)
        monkeypatch.setattr(os.path, 'exists', expanduser.exists)

        assert backup_mode_fs(
            backup_opt, 123456789, test_meta) is None

        backup_opt.__dict__['no_incremental'] = False
        with open(
                '/tmp/tar_metadata_test-hostname_test-backup-name_123456789_0', 'w') as fd:
            fd.write('testcontent\n')
        assert backup_mode_fs(
            backup_opt, 123456789, test_meta) is None


    def test_backup_mode_mongo(self, monkeypatch):

        # Class and other settings initialization
        test_meta = dict()
        backup_opt = BackupOpt1()
        fakemongo = FakeMongoDB()
        backup_opt.mode = 'mongo'
        fakeos = Os()
        fakere = FakeRe()
        fakeswiftclient = FakeSwiftClient()
        #fakeopen = FakeOpen()
        fakelvm = Lvm()
        fakemultiprocessing = FakeMultiProcessing()
        fakemultiprocessingqueue = fakemultiprocessing.Queue()
        fakemultiprocessingpipe = fakemultiprocessing.Pipe()
        fakemultiprocessinginit = fakemultiprocessing.__init__()

        monkeypatch.setattr(
            multiprocessing, 'Queue', fakemultiprocessingqueue)
        monkeypatch.setattr(
            multiprocessing, 'Pipe', fakemultiprocessingpipe)
        monkeypatch.setattr(
            multiprocessing, 'Process', fakemultiprocessing.Process)
        monkeypatch.setattr(
            multiprocessing, '__init__', fakemultiprocessinginit)
        monkeypatch.setattr(freezer.lvm, 'lvm_eval', fakelvm.lvm_eval)
        monkeypatch.setattr(pymongo, 'MongoClient', fakemongo)
        monkeypatch.setattr(os.path, 'exists', fakeos.exists)
        monkeypatch.setattr(re, 'search', fakere.search)
        monkeypatch.setattr(swiftclient, 'client', fakeswiftclient.client)
        #monkeypatch.setattr(__builtin__, 'open', fakeopen.open)

        assert backup_mode_mongo(
            backup_opt, 123456789, test_meta) is None

        fakemongo2 = FakeMongoDB2()
        monkeypatch.setattr(pymongo, 'MongoClient', fakemongo2)
        assert backup_mode_mongo(
            backup_opt, 123456789, test_meta) is True
