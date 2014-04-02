# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

import os
import unittest
import numpy as np
import appdirs
from gnodeclient.conf import Configuration

from gnodeclient.util.hdfio import store_array_data, read_array_data


class TestHDFIO(unittest.TestCase):
    """
    Unit tests for the hdf array data reading and writing.
    """

    def test_hdf5_io(self):
        basepath = appdirs.user_cache_dir(appname=Configuration.NAME, appauthor=Configuration.ATHOR)
        testpath = os.path.join(basepath, 'bla.hdf5')

        if not os.path.isdir(basepath):
            os.makedirs(basepath, 0o0750)

        testlist = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        testarray = np.array(testlist)

        store_array_data(testpath, testlist)
        self.assertTrue((read_array_data(testpath) == testarray).all())

        store_array_data(testpath, testarray)
        self.assertTrue((read_array_data(testpath) == testarray).all())

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestHDFIO))
    unittest.TextTestRunner(verbosity=2).run(suite)
