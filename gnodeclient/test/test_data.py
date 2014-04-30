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

from odml import Document, Section, Property, Value
from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, \
    RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, IrregularlySampledSignal

from gnodeclient.util.helper import random_str, random_base32
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
        miss = random_base32()
        data = Block(name=r_str("block"), description=r_str("desc"))
        self[Model.BLOCK] = TestData(loc, miss, data)

        loc = "/electrophysiology/segment/"
        miss = random_base32()
        data = Segment(name=r_str("segment"), description=r_str("desc"))
        self[Model.SEGMENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/eventarray/"
        leng = r_length()
        miss = random_base32()
        data = EventArray(times=r_times(leng), labels=r_labels(leng), name=r_str("eventarray"),
                          description=r_str("desc"))
        self[Model.EVENTARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/event/"
        miss = random_base32()
        data = Event(time=random() * 100 * pq.s, label=r_str("label"), name=r_str("event"),
                     description=r_str("description"))
        self[Model.EVENT] = TestData(loc, miss, data)

        loc = "/electrophysiology/epocharray/"
        leng = r_length()
        miss = random_base32()
        data = EpochArray(times=r_times(leng), durations=r_times(leng), labels=r_labels(leng),
                          name=r_str("epocharray"), description=r_str("description"))
        self[Model.EPOCHARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/epoch/"
        miss = random_base32()
        data = Epoch(time=random() * 100 * pq.s, duration=random() * 100 * pq.s, label=r_str("label"),
                     name=r_str("epoch"), description=r_str("description"))
        self[Model.EPOCH] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannelgroup/"
        leng = r_length()
        miss = random_base32()
        data = RecordingChannelGroup(channel_names=r_labels(leng, "chan"), channel_indexes=range(leng),
                                     name=r_str("recordingchannelgroup"), description="description")
        self[Model.RECORDINGCHANNELGROUP] = TestData(loc, miss, data)

        loc = "/electrophysiology/recordingchannel/"
        miss = random_base32()
        data = RecordingChannel(index=randint(1, 100), name=r_str("recordingchannel"), description="description")
        data.recordingchannelgroups = []
        self[Model.RECORDINGCHANNEL] = TestData(loc, miss, data)

        loc = "/electrophysiology/unit/"
        miss = random_base32()
        data = Unit(name=r_str("unit"), description="description")
        self[Model.UNIT] = TestData(loc, miss, data)

        loc = "/electrophysiology/spiketrain/"
        miss = random_base32()
        data = SpikeTrain(times=r_times(), t_stop=1000 * pq.s, name=r_str("spiketrain"), description="description")
        self[Model.SPIKETRAIN] = TestData(loc, miss, data)

        loc = "/electrophysiology/spike/"
        miss = random_base32()
        data = Spike(time=random() * 100 * pq.s, name=r_str("spike"), description="description", left_sweep=1 * pq.ms,
                     sampling_rate=1 * pq.kHz)
        self[Model.SPIKE] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignalarray/"
        miss = random_base32()
        data = AnalogSignalArray(signal=pq.Quantity(np.random.rand(3, 3), 'mV'), t_start=random() * 100 * pq.s,
                                 sampling_rate=1 * pq.kHz, name=r_str("analogsignalarray"), description="description")
        self[Model.ANALOGSIGNALARRAY] = TestData(loc, miss, data)

        loc = "/electrophysiology/analogsignal/"
        miss = random_base32()
        data = AnalogSignal(signal=pq.Quantity(np.random.rand(100), 'mV'), t_start=random() * 100 * pq.s,
                            sampling_rate=1 * pq.kHz, name=r_str("analogsignal"), description="description")
        self[Model.ANALOGSIGNAL] = TestData(loc, miss, data)

        loc = "/electrophysiology/irregularlysampledsignal/"
        miss = random_base32()
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


class TestAssets(object):

    @classmethod
    def generate(cls, session=None):
        return dict(cls.fake_ephys(session).items() +
                    cls.fake_metadata(session).items())

    @staticmethod
    def fake_metadata(session=None):
        def assign_dummy_properties(section):
            for j in range(randint(1, 2)):
                p = Property(name="prop %d" % j, value="value %d" % j)
                p._section = section
                v = p.value
                if session:
                    p = session.set(p)
                    v._property = p
                    v = session.set(v)
                section.append(p)
                metadata["property"].append(p)
                metadata["value"].append(v)

        metadata = {"document": [], "section": [], "property": [], "value": []}
        
        # documents
        url = "http://portal.g-node.org/odml/terminologies/v1.0/" \
              + "terminologies.xml"
        for i in range(2):
            params = {
                'author': "mister %d" % i,
                'version': 1.0,
                'repository': url,
            }
            obj = Document(**params)
            if session:
                obj = session.set(obj)
            metadata['document'].append(obj)

        # sections first level
        for i in range(4):
            doc = metadata['document'][0] if i < 2 else \
                metadata['document'][1]
            params = {
                'name': "%d-th section" % i,
                'type': "level #1",
                'parent': doc,
            }
            obj = Section(**params)
            if session:
                obj = session.set(obj)
            doc.append(obj)
            assign_dummy_properties(obj)
            metadata["section"].append(obj)

        # sections second level
        for i in range(4):
            sec = metadata["section"][0] if i < 2 else \
                metadata["section"][1]
            params = {
                'name': "%d-th section" % i,
                'type': "level #2",
                'parent': sec,
            }
            obj = Section(**params)
            if session:
                obj = session.set(obj)
            sec.append(obj)
            assign_dummy_properties(obj)
            metadata["section"].append(obj)

        return metadata

    @staticmethod
    def fake_ephys(session=None):
        
        ephys = {"block": [], "segment": [], "eventarray": [], "event": [],
                 "epocharray": [], "epoch": [], "recordingchannelgroup": [], 
                 "recordingchannel": [], "unit": [], "spiketrain": [], 
                 "analogsignalarray": [], "analogsignal": [], 
                 "irregularlysampledsignal": [], "spike": []}

        # blocks
        for i in range(2):
            params = {
                'name': "Local Field Potential and Spike Data %d" % (i + 1),
            }
            obj = Block(**params)
            if session:
                obj = session.set(obj)
            ephys["block"].append(obj)

        # RCGs
        for i in range(2):
            params = {
                'name': "Electrode group %d" % (i + 1),
            }
            obj = RecordingChannelGroup(**params)
            obj.block = ephys['block'][0]
            if session:
                obj = session.set(obj)
            ephys["recordingchannelgroup"].append(obj)
            ephys['block'][0].recordingchannelgroups.append(obj)

        # recording channels
        for i in range(2):
            params = {
                'name': "Electrode %d" % (i + 1),
                'index': (i + 1),
            }
            obj = RecordingChannel(**params)
            obj.recordingchannelgroups.append(ephys["recordingchannelgroup"][0])
            if session:
                obj = session.set(obj)
            ephys["recordingchannel"].append(obj)
            ephys["recordingchannelgroup"][0].recordingchannels.append(obj)

        # units
        for i in range(2):
            params = {
                'name': "SUA-LFP-unit %d" % (i + 1),
            }
            obj = Unit(**params)
            obj.recordingchannelgroup = ephys["recordingchannelgroup"][0]
            if session:
                obj = session.set(obj)
            ephys["recordingchannelgroup"][0].units.append(obj)
            ephys["unit"].append(obj)

        # segments
        for i in range(4):
            params = {
                'name': "Segment %d" % (i + 1),
            }
            obj = Segment(**params)
            obj.block = ephys['block'][0]
            if session:
                obj = session.set(obj)
            ephys['block'][0].segments.append(obj)
            ephys["segment"].append(obj)

        # event arrays
        for i in range(2):
            parent = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            params = {
                'name': "Event array %d" % (i + 1),
                'labels': np.array(['foo', 'bar'], dtype='S'),
                'times': np.array([1.46, 4.15]) * pq.ms,
            }
            obj = EventArray(**params)
            obj.segment = parent
            if session:
                obj = session.set(obj)
            parent.eventarrays.append(obj)
            ephys["eventarray"].append(obj)

        # events
        for i in range(2):
            parent = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            params = {
                'name': "Event %d" % (i + 1),
                'label': "Event label %d" % (i + 1),
                'time': 1.56 * pq.ms,
            }
            obj = Event(**params)
            obj.segment = parent
            if session:
                obj = session.set(obj)
            parent.events.append(obj)
            ephys["event"].append(obj)

        # epoch arrays
        for i in range(2):
            parent = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            params = {
                'name': "Epoch array %d" % (i + 1),
                'labels': np.array(['foo', 'bar'], dtype='S'),
                'times': np.array([1.46, 4.15]) * pq.ms,
                'durations': np.array([1.01, 1.03]) * pq.ms,
            }
            obj = EpochArray(**params)
            obj.segment = parent
            if session:
                obj = session.set(obj)
            parent.epocharrays.append(obj)
            ephys["epocharray"].append(obj)

        # epochs
        for i in range(2):
            parent = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            params = {
                'name': "Epoch %d" % (i + 1),
                'label': "Epoch label %d" % (i + 1),
                'time': 1.56 * pq.ms,
                'duration': 5.23 * pq.ms,
            }
            obj = Epoch(**params)
            obj.segment = parent
            if session:
                obj = session.set(obj)
            parent.epochs.append(obj)
            ephys["epoch"].append(obj)

        # spike trains
        for i in range(2):
            segment = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            unit = ephys['unit'][0] if i < 2 else ephys['unit'][1]
            params = {
                'name': "Spiketrain %d" % (i + 1),
                't_start': 0.56 * pq.ms,
                't_stop': 5.23 * pq.ms,
                'times': np.array([1.46, 4.15]) * pq.ms,
            }
            obj = SpikeTrain(**params)
            obj.segment = segment
            obj.unit = unit
            if session:
                obj = session.set(obj)
            segment.spiketrains.append(obj)
            unit.spiketrains.append(obj)
            ephys["spiketrain"].append(obj)

        # analog signal arrays
        for i in range(2):
            segment = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            rcg = ephys['recordingchannelgroup'][0] if i < 3 else ephys['recordingchannelgroup'][1]
            params = {
                'name': "ASA %d" % (i + 1),
                't_start': 1.56 * pq.ms,
                'sampling_rate': 10000.0 * pq.Hz,
                'signal': np.array([[1.46, 4.15], [2.98, 3.12]]) * pq.mV,
            }
            obj = AnalogSignalArray(**params)
            obj.segment = segment
            obj.recordingchannelgroup = rcg
            if session:
                obj = session.set(obj)
            segment.analogsignalarrays.append(obj)
            rcg.analogsignalarrays.append(obj)
            ephys["analogsignalarray"].append(obj)

        # analog signals
        for i in range(2):
            segment = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            rc = ephys['recordingchannel'][0] if i < 3 else ephys['recordingchannel'][1]
            params = {
                'name': "Analog signal %d" % (i + 1),
                't_start': 1.56 * pq.ms,
                'sampling_rate': 10000.0 * pq.Hz,
                'signal': np.array([1.46, 4.15]) * pq.mV,
            }
            obj = AnalogSignal(**params)
            obj.segment = segment
            obj.recordingchannel = rc
            if session:
                obj = session.set(obj)
            segment.analogsignals.append(obj)
            rc.analogsignals.append(obj)
            ephys["analogsignal"].append(obj)

        # irsa-s
        for i in range(2):
            segment = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            rc = ephys['recordingchannel'][0] if i < 3 else ephys['recordingchannel'][1]
            params = {
                'name': "Irregular signal %d" % (i + 1),
                't_start': 1.56 * pq.ms,
                'signal': np.array([1.46, 4.15]) * pq.mV,
                'times': np.array([3.05, 4.05]) * pq.ms,
            }
            obj = IrregularlySampledSignal(**params)
            obj.segment = segment
            obj.recordingchannel = rc
            if session:
                obj = session.set(obj)
            segment.irregularlysampledsignals.append(obj)
            rc.irregularlysampledsignals.append(obj)
            ephys["irregularlysampledsignal"].append(obj)

        # spikes
        for i in range(2):
            segment = ephys['segment'][0] if i < 2 else ephys['segment'][1]
            unit = ephys['unit'][0] if i < 2 else ephys['unit'][1]
            params = {
                'name': "Spike waveform %d" % (i + 1),
                'time': 1.56 * pq.ms,
                'sampling_rate': 10000.0 * pq.Hz,
                'left_sweep': 1.56 * pq.ms,
                'waveform': np.array([1.46, 4.15]) * pq.mV,
            }
            obj = Spike(**params)
            obj.segment = segment
            obj.unit = unit
            if session:
                obj = session.set(obj)
            segment.spikes.append(obj)
            unit.spikes.append(obj)
            ephys["spike"].append(obj)

        return ephys
