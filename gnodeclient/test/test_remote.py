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
from requests.exceptions import HTTPError
from gnodeclient.util.helper import id_from_location
from gnodeclient import *
from gnodeclient.test.test_data import TestAssets


class TestRestAPI(unittest.TestCase):
    """
    Unit tests for the session object.
    """

    def setUp(self):
        self.session = session.create(
            location="http://localhost:8000", username="bob", password="pass"
        )
        self.session.clear_cache()

        self.local_assets = TestAssets.generate()
        self.remote_assets = TestAssets.generate(self.session)

    def tearDown(self):
        for obj in self.remote_assets['document'] + self.remote_assets['block']:
            try:
                self.session.delete(obj)
            except HTTPError, e:
                if not e.response.status_code == 404:  # object already deleted
                    raise e

        session.close()

    def get_remote_objs(self, model_name):
        """ this assumes that 'select' method already works. in case of any
        bugs in 'select' operation this method will also fail """
        assets = self.remote_assets[model_name]
        filters = {
            'limit': 10,
            'id__in': ",".join([id_from_location(x.location) for x in assets])
        }
        return self.session.select(model_name, filters)

    def get_local_objs(self, model_name):
        return self.local_assets[model_name]

    def build_dummy_obj(self, model_name):
        template = self.get_local_objs(model_name)[0]

        model_obj = Model.create(model_name)
        fields = filter(  # all parent fields
            lambda x: model_obj.get_field(x).is_parent,
            [field_name for field_name in model_obj]
        )

        if model_name == 'recordingchannel':
            parent = self.get_remote_objs('recordingchannelgroup')[0]
            template.recordingchannelgroups.append(parent)

        if not fields:
            return template

        if model_name == 'section':
            template._parent = self.get_remote_objs('document')[0]

        elif model_name in 'property':
            parent = self.get_remote_objs('section')[0]
            parent.append(template)

        elif model_name == 'value':
            parent = self.get_remote_objs('property')[0]
            parent.append(template)

        else:
            for field_name in fields:
                #if field_name == 'metadata':
                #    parent = self.get_remote_objs('section')[0]
                #else:
                parent = self.get_remote_objs(field_name)[0]
                setattr(template, field_name, parent)

        return template

    # tests --------------------------------------------------------------------

    def test_select(self):
        for model_name in self.remote_assets.keys():
            data = self.remote_assets[model_name][0]
            results = self.get_remote_objs(model_name)

            msg = "No results for select('%s')!" % model_name
            self.assertTrue(len(results) > 0, msg)

            elem = results[randint(0, len(results) - 1)]

            msg = "Result has wrong type (%s)!" % type(elem)
            self.assertTrue(isinstance(elem, type(data)), msg)

    def test_get_by_id(self):
        for model_name, objects in self.remote_assets.items():

            location = objects[0].location
            result = self.session.get(location)

            msg = "The result of get(%s) should not be None!" % location
            self.assertIsNotNone(result, msg)
            self.assertEqual(result.location, location)

    def test_create(self):
        for model_name in self.local_assets.keys():

            obj = self.build_dummy_obj(model_name)
            result = self.session.set(obj)

            msg = "Create for the %s failed" % model_name
            self.assertTrue(hasattr(result, 'location'), msg)

    def zztest_update_fields(self):
        for model_name in self.local_assets.keys():
            pass

    def zztest_update_parent(self):
        for model_name in self.local_assets.keys():
            pass

    def zztest_update_data(self):
        for model_name in self.local_assets.keys():
            pass

    def test_delete(self):
        for model_name in self.remote_assets.keys():

            available = self.get_remote_objs(model_name)
            dead = available[-1]
            self.session.delete(dead)

            msg = "Object of type %s was not deleted" % model_name
            self.assertIsNone(self.session.get(dead.location), msg)

    def test_set_all(self):
        for model_name in ['document', 'block']:

            # create
            obj = self.local_assets[model_name][0]
            result = self.session.set_all(obj)

            msg = "Create for the %s failed" % model_name
            self.assertTrue(hasattr(result, 'location'), msg)

            # update
            obj = self.remote_assets[model_name][0]
            result = self.session.set_all(obj)

            msg = "Create for the %s failed" % model_name
            self.assertTrue(hasattr(result, 'location'), msg)

    def test_permissions(self):
        for model_name in ['document', 'block']:
            perms = [{
                "user": "/api/v1/user/user/neo/",
                "access_level": 2
            }]
            obj = self.remote_assets[model_name][0]

            old_perms = self.session.permissions(obj)

            new_perms = self.session.permissions(obj, perms)
            msg = "Permissions do not match, before: %s, after: %s" % \
                  (perms, new_perms)
            self.assertEqual(perms, new_perms, msg)

            new_perms = self.session.permissions(obj, old_perms)
            msg = "Permissions do not match, before: %s, after: %s" % \
                  (old_perms, new_perms)
            self.assertEqual(old_perms, new_perms, msg)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestRestAPI))
    unittest.TextTestRunner(verbosity=2).run(suite)
