"""
Basic test data
"""

from random import random, randint

import numpy as np
import quantities as pq

from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, \
                RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, \
                IrregularlySampledSignal

from gnode.utils import generate_id
from gnodeclient.model.rest_model import Models


def singleton(cls):
    """
    Singleton implementation (http://www.python.org/dev/peps/pep-0318/#examples)
    """

    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


def r_str(prefix, length=5):
    return prefix + '_' + generate_id(length)


def r_length():
    return randint(10, 1000)


def r_times(length=None):
    if length is None:
        length = r_length()
    return np.array([random() * 1000 for _ in xrange(length)]) * pq.s


def r_labels(length=None, label="label"):
    if length is None:
        length = r_length()
    return np.array([r_str(label) for _ in xrange(length)], dtype='S')


class TestData(object):
    """
    Unified store for test data
    """

    def __init__(self, base_location, missing_id, test_data, existing_data=None):
        self.base_location = base_location
        self.missing_id = missing_id
        self.test_data = test_data
        self.existing_data = existing_data


@singleton
class TestDataCollection(object):
    """
    A simple singleton dictionary of test data
    """

    def __init__(self):
        self.__data_sets = {}

        loc = "/electrophysiology/block/"
        miss = generate_id()
        data = Block(name=r_str("block"), description=r_str("desc"))
        self[Models.BLOCK] = TestData(loc, miss, data)

        loc = "/electrophysiology/segment/"
        miss = generate_id()
        data = Segment(name=r_str("segment"), description=r_str("desc"))
        self[Models.SEGMENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/eventarray/"
        leng = r_length()
        miss = generate_id()
        data = EventArray(times=r_times(leng), labels=r_labels(leng), name=r_str("eventarray"),
                          description=r_str("desc"))
        self[Models.EVENTARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/event/"
        miss = generate_id()
        data = Event(time=random() * 100 * pq.s, label=r_str("label"), name=r_str("event"), description=r_str("description"))
        self[Models.EVENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/epocharray/"
        leng = r_length()
        miss = generate_id()
        data = EpochArray(times=r_times(leng), durations=r_times(leng), labels=r_labels(leng),
                          name=r_str("epocharray"), description=r_str("description"))
        self[Models.EPOCHARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/epoch/"
        miss = generate_id()
        data = Epoch(time=random() * 100 * pq.s, duration=random() * 100 * pq.s, label=r_str("label"),
                     name=r_str("epoch"), description=r_str("description"))
        self[Models.EPOCH] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannelgroup/"
        leng = r_length()
        miss = generate_id()
        data = RecordingChannelGroup(channel_names=r_labels(leng, "chan"), channel_indexes=range(leng),
                                     name=r_str("recordingchannelgroup"), description="description")
        self[Models.RECORDINGCHANNELGROUP] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannel/"
        miss = generate_id()
        data = RecordingChannel(index=randint(1, 100), name=r_str("recordingchannel"), description="description")
        data.recordingchannelgroups = []
        self[Models.RECORDINGCHANNEL] = TestData(loc, miss, data)

        loc = "/electrophysiology/unit/"
        miss = generate_id()
        data = Unit(name=r_str("unit"), description="description")
        self[Models.UNIT] = TestData(loc, miss, data)

        loc = "/electrophysiology/spiketrain/"
        miss = generate_id()
        data = SpikeTrain(times=r_times(), t_stop=1000 * pq.s, name=r_str("spiketrain"), description="description")
        self[Models.SPIKETRAIN] = TestData(loc, miss, data)

        loc = "/electrophysiology/spike/"
        miss = generate_id()
        data = Spike(time=random() * 100 * pq.s, name=r_str("spike"), description="description")
        self[Models.SPIKE] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignalarray/"
        miss = generate_id()
        data = AnalogSignalArray(signal=pq.Quantity(np.random.rand(3, 3), 'mV'), t_start=random() * 100 * pq.s,
                                 sampling_period=0.1 * pq.s, name=r_str("analogsignalarray"), description="description")
        self[Models.ANALOGSIGNALARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignal/"
        miss = generate_id()
        data = AnalogSignal(signal=pq.Quantity(np.random.rand(100), 'mV'), t_start=random() * 100 * pq.s,
                            sampling_period=0.1 * pq.s, name=r_str("analogsignal"), description="description")
        self[Models.ANALOGSIGNAL] = TestData(loc, miss, data)

        loc = "/electrophysiology/irregularlysampledsignal/"
        miss = generate_id()
        leng = r_length()
        data = IrregularlySampledSignal(signal=pq.Quantity(np.random.rand(leng), 'mV'), times=r_times(leng),
                                        name=r_str("analogsignal"), description="description")
        self[Models.IRREGULARLYSAMPLEDSIGNAL] = TestData(loc, miss, data)


    #
    # Built-in functions
    #

    def __getitem__(self, item):
        return self.__data_sets[item]

    def __setitem__(self, key, value):
        if isinstance(value, TestData):
            self.__data_sets[key] = value
        else:
            raise ValueError("The value is not from the type TestData: %s!" % str(value))

    def __len__(self):
        return len(self.__data_sets)

    def __iter__(self):
        return iter(self.__data_sets)

    def __str__(self):
        return str(self.__data_sets)

    def __repr__(self):
        return repr(self.__data_sets)
