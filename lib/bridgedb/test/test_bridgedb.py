# -*- coding: utf-8 -*-
#
# This file is part of BridgeDB, a Tor bridge distribution system.
#
# :authors: Isis Lovecruft 0xA3ADB67A2CDB8B35 <isis@torproject.org>
#           please also see AUTHORS file
# :copyright: (c) 2013, Isis Lovecruft
#             (c) 2007-2013, The Tor Project, Inc.
#             (c) 2007-2013, all entities within the AUTHORS file
# :license: 3-Clause BSD, see LICENSE for licensing information

"""Unittests for the `bridgedb` commandline script."""

from __future__ import print_function

import os
import shutil
import signal
import time

from os.path import join as pjoin
from subprocess import Popen, PIPE

from twisted.python import log
from twisted.python.procutils import which
from twisted.trial import unittest

from bridgedb.test.util import fileCheckDecorator


class BridgeDBCliTest(unittest.TestCase):
    """Test the `bridgedb` command."""

    @fileCheckDecorator
    def doCopyFile(self, src, dst, description=None):
        shutil.copy(src, dst)

    @fileCheckDecorator
    def doMoveFile(self, src, dst, description=None):
        shutil.move(src, dst)

    def test_bridgedb_commands(self):
        print('')
        here       = os.getcwd()
        runDir     = pjoin(here, 'rundir')
        topDir     = here.rstrip('_trial_temp')
        scriptsDir = pjoin(topDir, 'scripts')

        # Create the lowest directory we need, and all its parents:
        os.makedirs(os.path.join(runDir, 'gnupghome'))

        conf      = pjoin(topDir, 'bridgedb.conf')
        confMoved = pjoin(runDir, 'bridgedb.conf')
        gpgFile   = pjoin(topDir, 'gnupghome', 'TESTING.subkeys.sec')
        gpgMoved  = pjoin(runDir, 'gnupghome', 'TESTING.subkeys.sec')
        certFile  = pjoin(topDir, 'cert')
        certMoved = pjoin(runDir, 'cert')
        keyFile   = pjoin(topDir, 'privkey.pem')
        keyMoved  = pjoin(runDir, 'privkey.pem')

        makeSSLCertScript = os.path.join(scriptsDir, 'make-ssl-cert')
        bridgedbScript    = which('bridgedb') # this returns a list

        self.doCopyFile(conf, confMoved, 'config')
        self.doCopyFile(gpgFile, gpgMoved, 'GPG test key')
        print("Running subcommands from directory:\n  %r" % runDir)
        print("Running %r..." % makeSSLCertScript)
        makeSSLCertProcess = Popen(makeSSLCertScript)
        makeSSLCertProcess.wait()
        self.doMoveFile(certFile, certMoved, 'certificate')
        self.doMoveFile(keyFile, keyMoved, 'SSL private key')

        self.assertTrue(os.path.isfile(bridgedbScript[0]),
                        "Couldn't find bridgedb script %r" % bridgedbScript[0])
        bridgedbScript = bridgedbScript[0]
        print("Running bridgedb script %r..." % bridgedbScript)

        os.chdir(runDir)  # we have to do this to get files to end up there
        print("Running `bridgedb mock' to generate mock bridge descriptors...")
        mockProc = Popen([bridgedbScript, 'mock', '-n', '50'])
        mockProcCode = mockProc.wait()
        print("`bridgedb mock' exited with status code %d" % int(mockProcCode))
        os.chdir(here)

        # See ticket #11216, cached-extrainfo* files should not be parsed
        # cumulatively.
        eidesc  = pjoin(runDir, 'cached-extrainfo')
        eindesc = pjoin(runDir, 'cached-extrainfo.new')
        self.doCopyFile(eindesc, eidesc, 'duplicated cached-extrainfo(.new)')

        print("Running `bridgedb' to test server startups...")
        bridgedbProc = Popen([bridgedbScript, '-r', runDir])
        time.sleep(30)
        bridgedbProc.send_signal(signal.SIGINT)
        bridgedbProcCode = bridgedbProc.wait()
        print("`bridgedb' exited with status code %d" % int(bridgedbProcCode))
        self.assertEqual(bridgedbProcCode, 0)
