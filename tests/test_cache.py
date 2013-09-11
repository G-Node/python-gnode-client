import unittest

import numpy as np
import quantities as pq

from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, \
    RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, \
    IrregularlySampledSignal
from gnode import session
from gnode.rest_model import Models

from test_data import TestDataCollection, r_times


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

            result = self.session.cache.pull(location)

            msg = "Pulled data not cached"
            self.assertIsNotNone(result, msg)

            self.session.cache.clear_cache()

    def test_02_pull_cascade(self):
        child_count = 4

        # prepare test data
        bl = Block("block_1")
        for i in range(child_count):
            seg = Segment(name="seg_%d" % i, index=i)
            bl.segments.append(seg)

            rcg = RecordingChannelGroup(name="gcg_%d" % i)
            bl.recordingchannelgroups.append(rcg)

            for j in range(child_count):
                rc = RecordingChannel(index=j, name="rc_%d_%d" % (i, j))
                rcg.recordingchannels.append(rc)

                sig = AnalogSignal(np.random.rand(100) * pq.mV, sampling_period=0.1 * pq.s, name="sig_%d_%d" % (i, j))
                rc.analogsignals.append(sig)
                seg.analogsignals.append(sig)

        # push data
        self.session.push(bl, cascade=True, force_update=True)
        self.session.cache.clear_cache()

        msg = "Failed to push data: %s!" % str(bl)
        self.assertTrue(hasattr(bl, "_gnode"), msg)

        # pull data
        location = bl._gnode["location"]
        bl_pulled = self.session.pull(bl._gnode["location"])

        msg = "Failed to pull data from location: %s!" % location
        self.assertIsNotNone(bl_pulled, msg)

        count = len(bl_pulled.segments)
        msg = "Segment count is %d but %d was expected" % (count, child_count)
        self.assertEqual(count, child_count, msg)

        count = len(bl_pulled.recordingchannelgroups)
        msg = "RecordingChannelGroup count is %d but %d was expected" % (count, child_count)
        self.assertEqual(count, child_count, msg)

        count = len(bl_pulled.recordingchannelgroups[0].recordingchannels)
        msg = "RecordingChannel count is %d but %d was expected" % (count, child_count)
        self.assertEqual(count, child_count, msg)

        count = len(bl_pulled.segments[0].analogsignals)
        msg = "AnalogSignal count is %d but %d was expected" % (count, child_count)
        self.assertEqual(count, child_count, msg)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestCache))
    unittest.TextTestRunner(verbosity=2).run(suite)
