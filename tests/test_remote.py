import unittest
from random import randint

from test_data import TestDataCollection

from gnode import session


class TestRemote(unittest.TestCase):

    data = None

    #
    # Test setup
    #

    @classmethod
    def setUpClass(cls):
        cls.data = TestDataCollection()

    def setUp(self):
        self.session = session.init()

    def tearDown(self):
        self.session.shutdown()

    #
    # Tests
    #

    def test_01_list_all(self):
        for name in TestRemote.data:
            results = self.session.select(name)

            msg = "No results for select('%s')!" % name
            self.assertTrue(len(results) > 0, msg)

            elem = results[randint(0, len(results) - 1)]

            msg = "Result has wrong type (%s)!" % type(elem)
            self.assertTrue(isinstance(elem, type(TestRemote.data[name].test_data)), msg)

            TestRemote.data[name].existing_data = elem

    def test_02_get_existing_by_id(self):
        for name in TestRemote.data:
            elem_id = TestRemote.data[name].existing_data._gnode['id']
            results = self.session.select(name, params={'id': elem_id})

            msg = "The query select(%s, param={'id': %s}) should have one result!" % (name, elem_id)
            self.assertEquals(len(results), 1, msg)
            # FIXME why are they not equal
            # self.assertEquals(results[0], TestRemote.data[name].existing_data)

    def test_03_get_missing_by_id(self):
        for name in TestRemote.data:
            elem_id = TestRemote.data[name].missing_id
            results = self.session.select(name, params={'id': elem_id})

            msg = "The query select(%s, param={'id': %s}) should be empty!" % (name, elem_id)
            self.assertEquals(len(results), 0, msg)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestRemote))
    unittest.TextTestRunner(verbosity=2).run(suite)
