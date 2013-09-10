import unittest
from random import randint

from test_data import TestDataCollection

from gnode import session


class TestRemote(unittest.TestCase):

    data = None

    #
    # Test setup
    #

    def setUp(self):
        self.session = session.init()
        self.data = TestDataCollection()

    def tearDown(self):
        self.session.shutdown()

    #
    # Tests
    #

    def test_01_select(self):
        for name in self.data:
            data = self.data[name]
            results = self.session.select(name, {'max_results': 10})

            msg = "No results for select('%s')!" % name
            self.assertTrue(len(results) > 0, msg)

            elem = results[randint(0, len(results) - 1)]

            msg = "Result has wrong type (%s)!" % type(elem)
            self.assertTrue(isinstance(elem, type(data.test_data)), msg)

            data.existing_data = elem

    def test_02_select_by_id(self):
        for name in self.data:
            data = self.data[name]
            elem_id = data.existing_data._gnode['id']
            results = self.session.select(name, params={'id': elem_id})

            msg = "The query select(%s, param={'id': %s}) should have one result!" % (name, elem_id)
            self.assertEquals(len(results), 1, msg)

            # FIXME why are they not equal
            # self.assertEquals(results[0], data.existing_data)

    def test_03_select_missing_by_id(self):
        for name in self.data:
            data = self.data[name]
            elem_id = data.missing_id
            results = self.session.select(name, params={'id': elem_id})

            msg = "The query select(%s, param={'id': %s}) should be empty!" % (name, elem_id)
            self.assertEquals(len(results), 0, msg)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestRemote))
    unittest.TextTestRunner(verbosity=2).run(suite)
