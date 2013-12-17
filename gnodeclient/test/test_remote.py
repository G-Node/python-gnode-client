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
from random import randint

from gnodeclient import *
from gnodeclient.test.test_data import TestDataCollection


class TestRemote(unittest.TestCase):
    """
    Unit tests for the session object.
    """

    data = None

    #
    # Test setup
    #

    def setUp(self):
        self.session = session.create(location="http://predata.g-node.org", username="bob", password="pass")
        self.session.clear_cache()
        self.data = TestDataCollection()

    def tearDown(self):
        session.close()

    #
    # Tests
    #

    def test_01_select(self):
        for name in self.data:
            data = self.data[name]
            results = self.session.select(name, {'max_results': 5})

            msg = "No results for select('%s')!" % name
            self.assertTrue(len(results) > 0, msg)

            elem = results[randint(0, len(results) - 1)]

            msg = "Result has wrong type (%s)!" % type(elem)
            self.assertTrue(isinstance(elem, type(data.test_data)), msg)

            data.existing_data = elem

    def test_02_get_by_id(self):
        for name in self.data:
            data = self.data[name]
            if data.existing_data is not None:
                location = data.existing_data.location
                result = self.session.get(location)

                msg = "The result of get(%s) should not be None!" % data.existing_data.location
                self.assertIsNotNone(result, msg)
            else:
                self.assertIsNotNone(data.existing_data, "No existing data for %s" % name)

    def test_03_get_missing_by_id(self):
        for name in self.data:
            data = self.data[name]
            location = Model.get_location(name) + "/" + data.missing_id
            result = self.session.get(location)

            msg = "The result of get(%s) should be None!" % location
            self.assertIsNone(result, msg)

    def test_04_set_delete(self):
        for name in self.data:
            data = self.data[name]
            first_result = self.session.set(data.test_data)

            msg = "Unable to save object %s" % str(data.test_data)
            self.assertTrue(hasattr(first_result, 'location'), msg)

            second_result = self.session.get(first_result.location)
            msg = "Unable to retrieve saved object from location: %s" % first_result.location
            self.assertIsNotNone(second_result, msg)

            self.session.delete(second_result)
            second_result = self.session.get(first_result.location)

            msg = "The result of get(%s) should be None!" % first_result.location
            self.assertIsNone(second_result, msg)

    def test_05_permissions(self):
        default_perms = {
            "safety_level": 1,
            "shared_with": {
                "anita": 1,
                "jeff": 2
            }
        }
        for name in self.data:
            data = self.data[name]
            obj = self.session.set(data.test_data)

            old_perms = self.session.permissions(obj)

            new_perms = self.session.permissions(obj, default_perms)
            msg = "Permissions do not match, before: %s, after: %s" % \
                  (default_perms, new_perms)
            self.assertEqual(default_perms, new_perms, msg)

            new_perms = self.session.permissions(obj, old_perms)
            msg = "Permissions do not match, before: %s, after: %s" % \
                  (old_perms, new_perms)
            self.assertEqual(old_perms, new_perms, msg)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestRemote))
    unittest.TextTestRunner(verbosity=2).run(suite)
