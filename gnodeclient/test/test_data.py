# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
Basic test data
"""

from random import random, randint

import numpy as np
import quantities as pq

from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, \
    RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, IrregularlySampledSignal

from gnodeclient.util.helper import random_str
from gnodeclient.model.models import Model


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
    return prefix + '_' + random_str(length)


def r_length():
    return randint(10, 1000)


def r_times(length=None):
    if length is None:
        length = r_length()
    return np.array([random() * 1000 for _ in range(length)]) * pq.s


def r_labels(length=None, label="label"):
    if length is None:
        length = r_length()
    return np.array([r_str(label) for _ in range(length)], dtype='S')


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
        miss = random_str()
        data = Block(name=r_str("block"), description=r_str("desc"))
        self[Model.BLOCK] = TestData(loc, miss, data)

        loc = "/electrophysiology/segment/"
        miss = random_str()
        data = Segment(name=r_str("segment"), description=r_str("desc"))
        self[Model.SEGMENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/eventarray/"
        leng = r_length()
        miss = random_str()
        data = EventArray(times=r_times(leng), labels=r_labels(leng), name=r_str("eventarray"),
                          description=r_str("desc"))
        self[Model.EVENTARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/event/"
        miss = random_str()
        data = Event(time=random() * 100 * pq.s, label=r_str("label"), name=r_str("event"),
                     description=r_str("description"))
        self[Model.EVENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/epocharray/"
        leng = r_length()
        miss = random_str()
        data = EpochArray(times=r_times(leng), durations=r_times(leng), labels=r_labels(leng),
                          name=r_str("epocharray"), description=r_str("description"))
        self[Model.EPOCHARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/epoch/"
        miss = random_str()
        data = Epoch(time=random() * 100 * pq.s, duration=random() * 100 * pq.s, label=r_str("label"),
                     name=r_str("epoch"), description=r_str("description"))
        self[Model.EPOCH] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannelgroup/"
        leng = r_length()
        miss = random_str()
        data = RecordingChannelGroup(channel_names=r_labels(leng, "chan"), channel_indexes=range(leng),
                                     name=r_str("recordingchannelgroup"), description="description")
        self[Model.RECORDINGCHANNELGROUP] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannel/"
        miss = random_str()
        data = RecordingChannel(index=randint(1, 100), name=r_str("recordingchannel"), description="description")
        data.recordingchannelgroups = []
        self[Model.RECORDINGCHANNEL] = TestData(loc, miss, data)

        loc = "/electrophysiology/unit/"
        miss = random_str()
        data = Unit(name=r_str("unit"), description="description")
        self[Model.UNIT] = TestData(loc, miss, data)

        loc = "/electrophysiology/spiketrain/"
        miss = random_str()
        data = SpikeTrain(times=r_times(), t_stop=1000 * pq.s, name=r_str("spiketrain"), description="description")
        self[Model.SPIKETRAIN] = TestData(loc, miss, data)

        loc = "/electrophysiology/spike/"
        miss = random_str()
        data = Spike(time=random() * 100 * pq.s, name=r_str("spike"), description="description", left_sweep=1 * pq.ms,
                     sampling_rate=1 * pq.kHz)
        self[Model.SPIKE] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignalarray/"
        miss = random_str()
        data = AnalogSignalArray(signal=pq.Quantity(np.random.rand(3, 3), 'mV'), t_start=random() * 100 * pq.s,
                                 sampling_rate=1 * pq.kHz, name=r_str("analogsignalarray"), description="description")
        self[Model.ANALOGSIGNALARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignal/"
        miss = random_str()
        data = AnalogSignal(signal=pq.Quantity(np.random.rand(100), 'mV'), t_start=random() * 100 * pq.s,
                            sampling_rate=1 * pq.kHz, name=r_str("analogsignal"), description="description")
        self[Model.ANALOGSIGNAL] = TestData(loc, miss, data)

        loc = "/electrophysiology/irregularlysampledsignal/"
        miss = random_str()
        leng = r_length()
        data = IrregularlySampledSignal(signal=pq.Quantity(np.random.rand(leng), 'mV'), times=r_times(leng),
                                        name=r_str("analogsignal"), description="description", t_start=0 * pq.s)
        self[Model.IRREGULARLYSAMPLEDSIGNAL] = TestData(loc, miss, data)

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
