"""
Model definitions for the G-Node REST api.
"""
from model import Model, Field


class Models:
    """
    Just a class that defines some constants and a static factory method
    for models.

    Example:
    >>> signal = Models.create(Models.ANALOGSIGNAL)
    >>> signal.id = "id"
    """

    DATAFILE = "datafile"
    SECTION = "section"
    PROPERTY = "property"
    VALUE = "value"
    BLOCK = "block"
    SEGMENT = "segment"
    EVENTARRAY = "eventarray"
    EVENT = "event"
    EPOCHARRAY = "epocharray"
    EPOCH = "epoch"
    RECORDINGCHANNELGROUP = "recordingchannelgroup"
    RECORDINGCHANNEL = "recordingchannel"
    UNIT = "unit"
    SPIKETRAIN = "spiketrain"
    SPIKE = "spike"
    ANALOGSIGNALARRAY = "analogsignalarray"
    ANALOGSIGNAL = "analogsignal"
    IRREGULARLYSAMPLEDSIGNAL = "irregularlysampledsignal"

    _MODEL_MAP = {}

    @classmethod
    def create(cls, type_name):
        return cls._MODEL_MAP[type_name]()

    @classmethod
    def exists(cls, type_name):
        return type_name in cls._MODEL_MAP

    @classmethod
    def location(cls, type_name):
        if type_name == cls.DATAFILE:
            # TODO check if this is right
            return 'files'
        elif type_name in (cls.SECTION, cls.PROPERTY, cls.VALUE):
            return 'metadata/' + type_name
        else:
            return 'electrophysiology/' + type_name


class QuantityModel(Model):
    """Represents a value with a unit"""
    data = Field(default=0)
    units = Field(type=str)


class RestResult(Model):
    """Basic model for all kinds of results from the rest API"""
    id = Field(type=str)
    guid = Field(type=str)
    permalink = Field(type=str)
    location = Field(type=str)
    model = Field(type=str)

    def __str__(self):
        template = "<RestResult: model=%s, location=%s%s>"
        name_str = ""
        if self.get_field('name') is not None:
            name_str = ", name=%s" % self['name']
        return template % (self.model, self.location, name_str)


class SectionModel(RestResult):
    model = Field(type=str, default=Models.SECTION)
    name = Field(type=str, optional=False)
    description = Field(type=str)

    parent = Field(is_parent=True, type_info=Models.SECTION)
    properties = Field(is_child=True, type=list, type_info=Models.PROPERTY)

Models._MODEL_MAP[Models.SECTION] = SectionModel


class PropertyModel(RestResult):
    model = Field(type=str, default=Models.PROPERTY)
    name = Field(type=str, optional=False)

    parent = Field(is_parent=True, type_info=Models.SECTION)
    values = Field(is_child=True, optional=False, type=list, type_info=Models.VALUE)

Models._MODEL_MAP[Models.PROPERTY] = PropertyModel


class ValueModel(RestResult):
    model = Field(type=str, default=Models.VALUE)
    value = Field(type=str, optional=False)

    parent = Field(is_parent=True, type_info=Models.PROPERTY)

Models._MODEL_MAP[Models.VALUE] = ValueModel


class BlockModel(RestResult):
    model = Field(type=str, default=Models.BLOCK)
    name = Field(type=str)
    index = Field(type=int, default=0)
    description = Field(type=str)

    recordingchannelgroups = Field(is_child=True, type=list, type_info=Models.RECORDINGCHANNELGROUP)
    segments = Field(is_child=True, type=list, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.BLOCK] = BlockModel


class SegmentModel(RestResult):
    model = Field(type=str, default=Models.SEGMENT)
    name = Field(type=str, default="")
    index = Field(default=0)

    block = Field(is_parent=True, type_info=Models.BLOCK)

    analogsignals = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNAL)
    irregularlysampledsignals = Field(is_child=True, type=list, type_info=Models.IRREGULARLYSAMPLEDSIGNAL)
    analogsignalarrays = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNALARRAY)
    spiketrains = Field(is_child=True, type=list, type_info=Models.SPIKETRAIN)
    spikes = Field(is_child=True, type=list, type_info=Models.SPIKE)
    events = Field(is_child=True, type=list, type_info=Models.EVENT)
    epochs = Field(is_child=True, type=list, type_info=Models.EPOCH)

Models._MODEL_MAP[Models.SEGMENT] = SegmentModel


class EventArrayModel(RestResult):
    model = Field(type=str, default=Models.EVENTARRAY)
    name = Field(type=str, default="")
    description = Field(type=str)

    times = Field(optional=False, type=QuantityModel, type_info="datafile")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EVENTARRAY] = EventArrayModel


class EventModel(RestResult):
    model = Field(type=str, default=Models.EVENT)
    name = Field(type=str, default="")
    description = Field(type=str)

    time = Field(optional=False, type=QuantityModel, type_info="data")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EVENT] = EventModel


class EpochArrayModel(RestResult):
    model = Field(type=str, default=Models.EPOCHARRAY)
    name = Field(type=str, default="")
    description = Field(type=str)

    times = Field(optional=False, type=QuantityModel, type_info="datafile")
    durations = Field(optional=False, type=QuantityModel, type_info="datafile")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EPOCHARRAY] = EpochArrayModel


class EpochModel(RestResult):
    model = Field(type=str, default=Models.EPOCH)
    name = Field(type=str, default="")
    description = Field(type=str)
    label = Field(optional=False, type=str, default="")

    time = Field(optional=False, type=QuantityModel, type_info="data")
    duration = Field(optional=False, type=QuantityModel, type_info="data")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EPOCH] = EpochModel


class RecordingChannelGroupModel(RestResult):
    model = Field(type=str, default=Models.RECORDINGCHANNELGROUP)
    name = Field(type=str, default="")
    description = Field(type=str)

    block = Field(is_parent=True, type_info=Models.BLOCK)
    units = Field(is_child=True, type=list, type_info=Models.UNIT)
    recordingchannels = Field(is_child=True, type=list, type_info=Models.RECORDINGCHANNEL)
    analogsignalarrays = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNALARRAY)

Models._MODEL_MAP[Models.RECORDINGCHANNELGROUP] = RecordingChannelGroupModel


class RecordingChannelModel(RestResult):
    model = Field(type=str, default=Models.RECORDINGCHANNEL)
    name = Field(type=str, default="")
    description = Field(type=str)

    recordingchannelgroups = Field(is_child=True, type_info=Models.RECORDINGCHANNELGROUP)
    analogsignals = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNAL)
    irregularlysampledsignals = Field(is_child=True, type=list, type_info=Models.IRREGULARLYSAMPLEDSIGNAL)

Models._MODEL_MAP[Models.RECORDINGCHANNEL] = RecordingChannelModel


class UnitModel(RestResult):
    model = Field(type=str, default=Models.UNIT)
    name = Field(type=str, default="")
    description = Field(type=str)

    recordingchannelgroup = Field(is_parent=True, type_info=Models.RECORDINGCHANNELGROUP)
    spikes = Field(is_child=True, type=list, type_info=Models.SPIKE)
    spiketrains = Field(is_child=True, type=list, type_info=Models.SPIKETRAIN)

Models._MODEL_MAP[Models.UNIT] = UnitModel


class SpikeTrainModel(RestResult):
    model = Field(type=str, default=Models.SPIKETRAIN)
    name = Field(type=str, default="")
    description = Field(type=str)

    t_start = Field(type=QuantityModel, type_info="data")
    t_stop = Field(optional=False, type=QuantityModel, type_info="data")
    times = Field(optional=False, type=QuantityModel, type_info="datafile")
    waveforms = Field(type=QuantityModel, type_info="datafile")

    unit = Field(is_parent=True, type_info=Models.UNIT)
    segment = Field(is_parent=True, type_info=Models.SEGMENT)


Models._MODEL_MAP[Models.SPIKETRAIN] = SpikeTrainModel


class SpikeModel(RestResult):
    model = Field(type=str, default=Models.SPIKE)
    name = Field(type=str, default="")
    description = Field(type=str)

    time = Field(optional=False, type=QuantityModel, type_info="data")
    left_sweep = Field(type=QuantityModel, type_info="data")
    sampling_rate = Field(type=QuantityModel, type_info="data")
    waveform = Field(type=QuantityModel, type_info="datafile")

    unit = Field(is_parent=True, type_info=Models.UNIT)
    segment = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.SPIKE] = SpikeModel


class AnalogsignalArrayModel(RestResult):
    model = Field(type=str, default=Models.ANALOGSIGNALARRAY)
    name = Field(type=str, default="")
    description = Field(type=str)

    t_start = Field(type=QuantityModel, type_info="data")
    sampling_rate = Field(optional=False, type=QuantityModel, type_info="data")
    signal = Field(optional=False, type=QuantityModel, type_info="datafile")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)
    recordingchannelgroup = Field(is_parent=True, type_info=Models.RECORDINGCHANNELGROUP)

Models._MODEL_MAP[Models.ANALOGSIGNALARRAY] = AnalogsignalArrayModel


class AnalogsignalModel(RestResult):
    model = Field(type=str, default=Models.ANALOGSIGNAL)
    name = Field(type=str, default="")
    description = Field(type=str)

    t_start = Field(type=QuantityModel, type_info="data")
    sampling_rate = Field(optional=False, type=QuantityModel, type_info="data")
    signal = Field(optional=False, type=QuantityModel, type_info="datafile")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)
    recordingchannel = Field(is_parent=True, type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.ANALOGSIGNAL] = AnalogsignalModel


class IrregularlySampledSignalModel(RestResult):
    model = Field(type=str, default=Models.IRREGULARLYSAMPLEDSIGNAL)
    name = Field(type=str, default="")
    description = Field(type=str)
    
    t_start = Field(type=QuantityModel, type_info="data")
    signal = Field(optional=False, type=QuantityModel, type_info="datafile")
    times = Field(optional=False, type=QuantityModel, type_info="datafile")

    segment = Field(is_parent=True, type_info=Models.SEGMENT)
    recordingchannel = Field(is_parent=True, type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.IRREGULARLYSAMPLEDSIGNAL] = IrregularlySampledSignalModel
