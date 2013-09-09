import unittest


class TestCache(unittest.TestCase):

    def test_01(self):
        self.failUnlessEqual(1, 1)

    def test_02(self):
        self.failUnlessEqual(2, 2)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestCache))
    unittest.TextTestRunner(verbosity=2).run(suite)
