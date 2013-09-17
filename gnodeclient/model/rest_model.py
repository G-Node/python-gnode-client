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



class ValueModel(Model):
    """Represents a value with a unit"""
    data = Field()
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
    """Model for segment"""
    model = Field(type=str, default=Models.SEGMENT)
    name = Field(type=str, default="")
    index = Field(default=0)

    block = Field(is_parent=True, type_info=Models.BLOCK)

    analogsignals = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNAL)
    #irregularlysampledsignals = Field(is_child=True, type=list, type_info=Models.IRREGULARLYSAMPLEDSIGNAL)
    #analogsignalarrays = Field(is_child=True, type=list, type_info=Models.ANALOGSIGNALARRAY)
    #spiketrains = Field(is_child=True, type=list, type_info=Models.SPIKETRAIN)
    #spikes = Field(is_child=True, type=list, type_info=Models.SPIKE)
    #events = Field(is_child=True, type=list, type_info=Models.EVENT)
    #epochs = Field(is_child=True, type=list, type_info=Models.EPOCH)

Models._MODEL_MAP[Models.SEGMENT] = SegmentModel


class AnalogsignalModel(RestResult):
    """Model for analogsignal"""
    model = Field(type=str, default=Models.ANALOGSIGNAL)
    name = Field(type=str, default="")
    t_start = Field(type=ValueModel, type_info="data")
    sampling_rate = Field(optional=False, type=ValueModel, type_info="data")
    signal = Field(optional=False, type=ValueModel, type_info="datafile")

    segment = Field(is_parent=True, type=str, type_info=Models.SEGMENT)
    #recordingchannel = Field(is_parent=True, type=str, type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.ANALOGSIGNAL] = AnalogsignalModel
