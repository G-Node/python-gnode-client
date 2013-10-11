#!/usr/bin/env python

# From the project root run the tests as shown below:
# > PYTHONPATH="./" python tests/test_all.py

import unittest
from gnodeclient.test.test_hdfio import TestHDFIO


class TestAll(unittest.TestSuite):

    def __init__(self):
        super(TestAll, self).__init__()
        self.addTests(unittest.makeSuite(TestHDFIO))

    def test(self, verbosity=2):
        unittest.TextTestRunner(verbosity=verbosity).run(self)


if __name__ == "__main__":
    TestAll().test()
