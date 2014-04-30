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

from random import randint

import numpy as np
import quantities as pq

from odml import Document, Section, Property
from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, \
    RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, IrregularlySampledSignal


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
