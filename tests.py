#!/usr/bin/env python

import unittest
import datetime
import random
import quantities as pq
import numpy as np
import session, utils
import neo


from odml.property import BaseProperty as Property
from models import models_map

classes_necessary_attributes = {}
for k, v in neo.description.classes_necessary_attributes.items():
    classes_necessary_attributes[k.lower()] = v

classes_recommended_attributes = {}
for k, v in neo.description.classes_recommended_attributes.items():
    classes_recommended_attributes[k.lower()] = v

many_to_one_relationship = {}
for k, v in neo.description.many_to_one_relationship.items():
    many_to_one_relationship[k.lower()] = v

RANDOM_VALUES = {
    'labels':           ['foo' for x in range(np.random.randint(10))],
    'channel_names':    ['foo' for x in range(np.random.randint(10))],
    'channel_indexes':  [np.random.randint(10) for x in range(10)],
    'waveforms':        pq.Quantity(np.random.rand(3,3,3), 'mV'),
    'waveform':         pq.Quantity(np.random.rand(3,3), 'mV'),
    'durations':        pq.Quantity(np.random.rand(10), 'mV'),
    'signal':           pq.Quantity(np.random.rand(100), 'mV'),
    'times':            pq.Quantity(np.random.rand(100), 'mV'),
    'values':           pq.Quantity(np.random.rand(100), 'mV'),
    't_start':          pq.Quantity(np.random.rand(1)[0], 's'),
    'duration':         pq.Quantity(np.random.rand(1)[0] * 10, 's'),
    't_stop':           pq.Quantity(np.random.rand(1)[0] * 100, 's'),
    'left_sweep':       pq.Quantity(np.random.rand(1)[0], 's'),
    'time':             pq.Quantity(np.random.rand(1)[0], 's'),
    'coordinate':       pq.Quantity(np.random.rand(1)[0]),
    'sampling_rate':    pq.Quantity(round(np.random.rand(1) * 10000), 'Hz'),
    'index':            np.random.randint(10),
    'channel_index':    np.random.randint(10),
    'file_datetime':    datetime.datetime.now(),
    'rec_datetime':     datetime.datetime.now(),
    'label':            'foo',
    'description':      'bar',
    'file_origin':      'some reference to the original file',
    'name':             'foobar',
}


class BaseTest(unittest.TestCase):
	"""BaseTest class for all tests"""
	
	def setUp(self):
		self.g = session.init()

	def tearDown(self):
		self.g.shutdown()


class Tests( BaseTest ):

    def test_ls(self):
        """ test basic browser listing does not raise errors """
        for model_name in self.g._meta.model_names:
            self.g.ls(model_name)


    def test_create_metadata(self):
        """ test creation of odML metadata objects """

        template = random.choice(self.g.terminologies)
        s1_orig = template.clone()
        s1_orig.name = 'foobar'

        p1 = Property('Author', ['Markus', 'Thomas'], s1_orig)
        p2 = Property('Location', 'Philipps-Universitaet Marburg', s1_orig)

        s1_orig.append( p1 )
        s1_orig.append( p2 )

        self.g.sync(s1_orig, cascade=True) # sync all metadata

        sections = self.g.select('section', {'parent_section__isnull': 1})
        sections.sort(key=lambda x: x._gnode['id'], reverse=True)
        s1_new = sections[0]

        s1_orig._gnode['fields'].pop('guid')
        s1_new._gnode['fields'].pop('guid')
        self.assertEqual(s1_orig._gnode, s1_new._gnode)


    def test_create_data(self):
        """ test creation of NEO data objects """
        ordered_classes_tuple = (
            ("block", 1),
            ("segment", lambda: np.random.randint(2, 4)),
            ("recordingchannelgroup", lambda: np.random.randint(1, 2)),
            ("recordingchannel", lambda: np.random.randint(1, 4)),
            ("unit", lambda: np.random.randint(1, 2)),
            ("spike", lambda: np.random.randint(1, 2)),
            ("eventarray", lambda: np.random.randint(1, 4)),
            ("event", lambda: np.random.randint(1, 4)),
            ("epocharray", lambda: np.random.randint(1, 4)),
            ("epoch", lambda: np.random.randint(1, 4)),
            ("spiketrain", lambda: np.random.randint(1, 4)),
            ("analogsignalarray", lambda: np.random.randint(1, 4)),
            ("analogsignal", lambda: np.random.randint(1, 4)),
            ("irsaanalogsignal", lambda: np.random.randint(1, 4))
        )

        collector = {}
        for k in dict(ordered_classes_tuple).keys():
            collector[k] = []

        for model_name, amount_func in ordered_classes_tuple: # for every NEO object type, order!!
            for i in xrange( amount_func() ): # several objects of every type
                cls = models_map[ model_name ]
                params = {}

                required = classes_necessary_attributes[model_name]
                recommended = classes_recommended_attributes[model_name]

                for attr in required + recommended:
                    if attr in required or random.choice([True, False]):
                        params[attr[0]] = RANDOM_VALUES[attr[0]]

                obj = cls( **params )

                # add parents
                if many_to_one_relationship.has_key(model_name):
                    for par_type in many_to_one_relationship[model_name]:
                        parent = random.choice(collector[par_type])
                        setattr(obj, par_type.lower(), parent)
                        getattr(parent, model_name + 's').append(obj)

                # take care: M2Ms are ignored

        self.g.sync(collector['block'][0], cascade=True)

        blocks = self.g.select('block')
        blocks.sort(key=lambda x: x._gnode['id'], reverse=True)
        b = self.g.pull(blocks[0]._gnode['location'])

        # TODO traverse the tree here
        #self.assertEqual(b._gnode, collector['block'][0]._gnode)


    def test_pull_sync(self):
        a1 = self.g.pull('/eph/seg/1')
        self.g.sync( a1, cascade=True )

    """
    def test_section_block_connection(self):
        pass

    def zztest_pull(self):
        s1_orig = self.g.pull('/mtd/sec/1')

    def test_unicode(self):
        pass

    def test_data_caching(self):
        pass

    def test_select_performance(self):
        pass

    def test_pull_performance(self):
        pass

    def test_sync_performance(self):
        pass
    """


if __name__ == '__main__':
	unittest.main()
