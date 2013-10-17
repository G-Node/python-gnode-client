"""
In this module some extensions to the Native classes (Neo, odML) are defined.
"""

from odml import Section, Property, Value
from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, RecordingChannel, \
    Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, IrregularlySampledSignal


class LocationMixIn():
    pass


class MetadataMixIn():
    pass


class SectionMixIn():
    pass


class BlockMixIn():
    pass


#class nSection(Section):
#    pass