# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import print_function, absolute_import, division

import unittest
from gnodeclient.test.test_data import TestAssets
from gnodeclient.result.result_driver import NativeDriver
from gnodeclient.store.dumper import Dumper
import h5py
import os


class TestDumper(unittest.TestCase):
    """
    Unit tests for the Dumper module.
    """

    def setUp(self):
        self.local_assets = TestAssets.generate()

    def test_dump(self):
        dumper = Dumper(NativeDriver(None))
        path = dumper.dump(self.local_assets['block'][0])

        f = h5py.File(path, 'r')
        self.assertTrue(len(f.values()) > 0)

        for name, group in f.items():
            self.assertTrue(group['json'] is not None)

        # TODO write real assertions

        f.close()
        os.remove(path)

    def test_load(self):
        pass


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestDumper))
    unittest.TextTestRunner(verbosity=2).run(suite)