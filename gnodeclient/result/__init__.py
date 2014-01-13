
from gnodeclient.result.adapt_odml import *
from gnodeclient.result.adapt_neo import *


class Native(object):
    """
    A class containing natively supported models.
    """
    SECTION = Section
    PROPERTY = Property
    VALUE = Value
    BLOCK = Block
    SEGMENT = Segment
    EVENTARRAY = EventArray
    EVENT = Event
    EPOCHARRAY = EpochArray
    EPOCH = Epoch
    RECORDINGCHANNELGROUP = RecordingChannelGroup
    RECORDINGCHANNEL = RecordingChannel
    UNIT = Unit
    SPIKETRAIN = SpikeTrain
    SPIKE = Spike
    ANALOGSIGNALARRAY = AnalogSignalArray
    ANALOGSIGNAL = AnalogSignal
    IRREGULARLYSAMPLEDSIGNAL = IrregularlySampledSignal