#!/usr/bin/env python

# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

# From the project root run the tests as shown below:
# > PYTHONPATH="./" python tests/test_all.py

import unittest
from gnodeclient.test.test_hdfio import TestHDFIO
from gnodeclient.test.test_remote import TestRestAPI
from gnodeclient.test.test_dumper import TestDumper


class TestAll(unittest.TestSuite):

    def __init__(self):
        super(TestAll, self).__init__()
        self.addTests(unittest.makeSuite(TestDumper))
        self.addTests(unittest.makeSuite(TestHDFIO))
        self.addTests(unittest.makeSuite(TestRestAPI))

    def test(self, verbosity=2):
        unittest.TextTestRunner(verbosity=verbosity).run(self)


if __name__ == "__main__":
    TestAll().test()
