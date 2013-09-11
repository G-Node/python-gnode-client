import unittest

from test_data import TestDataCollection

from gnode import session


class TestCache(unittest.TestCase):
    """
    Unit tests for the session and cache object that focus on the functionality
    concerning local data.

    Tested methods:
    Session.pull()
    Cache.?
    """

    data = None

    #
    # Test setup
    #

    def setUp(self):
        self.session = session.init()
        self.data = TestDataCollection()
        for name in self.data:
            results = self.session.select(name, {'max_results': 1})
            if len(results) == 1:
                self.data.existing_data = results[0]
            else:
                raise RuntimeError("Failed to load test data")

    def tearDown(self):
        self.session.shutdown()

    #
    # Tests
    #

    def test_01_pull(self):
        for name in self.data:
            data = self.data[name]

            testdata = self.session.select(name, {'max_results': 1})
            if len(testdata) == 1:
                data.existing_data = testdata[0]
            else:
                raise RuntimeError("Failed to load test data")

            location = data.existing_data._gnode['location']
            result = self.session.pull(location=location, cascade=False)

            msg = "Failed to pull data from locaction: %s" % location
            self.assertIsNotNone(result, msg)

            result = self.session.cache.get_data(location)

            msg = "Pulled data not cached"
            self.assertIsNotNone(result, msg)

            self.session.cache.clear_cache()

    def test_02(self):
        self.failUnlessEqual(2, 2)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestCache))
    unittest.TextTestRunner(verbosity=2).run(suite)
