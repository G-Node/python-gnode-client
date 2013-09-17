#!/usr/bin/env python

# From the project root run the tests as shown below:
# > PYTHONPATH="./" python tests/test_all.py

import unittest
from gnodeclient.test.test_remote import TestRemote
from gnodeclient.test.test_cache import TestCache


class TestAll(unittest.TestSuite):

    def __init__(self):
        super(TestAll, self).__init__()
        self.addTests(unittest.makeSuite(TestRemote))
        self.addTests(unittest.makeSuite(TestCache))

    def test(self, verbosity=2):
        unittest.TextTestRunner(verbosity=verbosity).run(self)


if __name__ == "__main__":
    TestAll().test()
