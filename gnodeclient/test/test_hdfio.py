import unittest
import numpy as np

from gnodeclient.util.hdfio import store_array_data, read_array_data


class TestHDFIO(unittest.TestCase):
    """
    Unit tests for the hdf array data reading and writing.
    """

    def test_all(self):
        testpath = '/tmp/bla.hdf5'
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
