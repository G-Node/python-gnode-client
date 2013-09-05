"""
Model definitions for the G-Node REST api.
"""

from numbers import Number
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
    IRREGULARLYSAMPLESSIGNAL = "irregularlysamplessignal"

    _MODELMAP = {}

    @classmethod
    def create(cls, type_name):
        return cls._MODELMAP[type_name]()


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
    data = TypedField(optional=False, type=Number)
    units = TypedField(optional=False, type=str)


class RestResult(Model):
    """Basic model for all kinds of results from the rest API"""
    id = TypedField(optional=False, type=str)
    permalink = TypedField(optional=False, type=str)
    location = TypedField(optional=False, type=str)
    type = TypedField(optional=False, type=str)

    def __str__(self):
        template = "<RestResult: type=%s, location=%s%s>"
        name_str = ""
        if self.get_field('name') is not None:
            name_str = ", name=%s" % self['name']
        return template % (self.type, self.location, name_str)


class AnalogsignalModel(RestResult):
    """An example model for analogsignal"""
    type = TypedField(optional=False, type=str, default="analogsignal")
    name = TypedField(type=str, default="")
    sampling_rate = TypedField(optional=False, type=ValueModel, type_info="data")
    t_start = TypedField(optional=False, type=ValueModel, type_info="data")
    # TODO define type more precisely
    segment = TypedField(is_parent=True, type=RestResult, type_info="segment")
    recordingchannel = TypedField(is_parent=True, type=RestResult, type_info="recordingchannel")

Models._MODELMAP[Models.ANALOGSIGNAL] = AnalogsignalModel
