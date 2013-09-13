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


class TypedField(Field):
    """
    A field that checks the type for compatibility.
    """

    def check(self, value):
        if isinstance(value, self.desc.type):
            return True
        else:
            return False


class ValueModel(Model):
    """Represents a value with a unit"""
    data = Field(optional=False)
    units = TypedField(optional=False, type=str)


class RestResult(Model):
    """Basic model for all kinds of results from the rest API"""
    id = TypedField(optional=False, type=str)
    guid = TypedField(optional=False, type=str)
    permalink = TypedField(optional=False, type=str)
    location = TypedField(optional=False, type=str)
    model = TypedField(optional=False, type=str)

    def __str__(self):
        template = "<RestResult: model=%s, location=%s%s>"
        name_str = ""
        if self.get_field('name') is not None:
            name_str = ", name=%s" % self['name']
        return template % (self.model, self.location, name_str)


class SegmentModel(RestResult):
    """Model for segment"""
    model = TypedField(optional=False, type=str, default=Models.SEGMENT)
    name = TypedField(type=str, default="")
    index = TypedField(default=0)

    block = TypedField(is_parent=True, type=str, type_info=Models.BLOCK)

    analogsignals = TypedField(is_child=True, type=list, type_info=Models.ANALOGSIGNAL)
    #irregularlysampledsignals = TypedField(is_child=True, type=list, type_info=Models.IRREGULARLYSAMPLEDSIGNAL)
    #analogsignalarrays = TypedField(is_child=True, type=list, type_info=Models.ANALOGSIGNALARRAY)
    #spiketrains = TypedField(is_child=True, type=list, type_info=Models.SPIKETRAIN)
    #spikes = TypedField(is_child=True, type=list, type_info=Models.SPIKE)
    #events = TypedField(is_child=True, type=list, type_info=Models.EVENT)
    #epochs = TypedField(is_child=True, type=list, type_info=Models.EPOCH)

Models._MODEL_MAP[Models.SEGMENT] = SegmentModel


class AnalogsignalModel(RestResult):
    """Model for analogsignal"""
    model = TypedField(optional=False, type=str, default=Models.ANALOGSIGNAL)
    name = TypedField(type=str, default="")
    sampling_rate = TypedField(optional=False, type=ValueModel, type_info="data")
    t_start = TypedField(optional=False, type=ValueModel, type_info="data")
    signal = TypedField(type=ValueModel, type_info="datafile")

    segment = TypedField(is_parent=True, type=str, type_info=Models.SEGMENT)
    recordingchannel = TypedField(is_parent=True, type=str, type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.ANALOGSIGNAL] = AnalogsignalModel
