from __future__ import print_function, absolute_import, division

from gnodeclient.util.declarative_models import Field, Model
from gnodeclient.model.model_fields import FTyped


class Models(object):

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
        """
        Creates an instance of the model class matching the type name.

        :param type_name: The name of the model class.
        :type type_name: str

        :returns: An instance of the respective model class.
        :rtype: RestResult
        """
        return cls._MODEL_MAP[type_name]()

    @classmethod
    def exists(cls, type_name):
        return type_name in cls._MODEL_MAP

    @classmethod
    def location(cls, type_name):
        if type_name == cls.DATAFILE:
            return 'datafiles/datafile'
        elif type_name in (cls.SECTION, cls.PROPERTY, cls.VALUE):
            return 'metadata/' + type_name
        else:
            return 'electrophysiology/' + type_name


class RestResult(Model):
    """Basic model for all kinds of results from the rest API"""
    id          = Field(field_type=str)
    guid        = Field(field_type=str)
    permalink   = Field(field_type=str)
    location    = Field(field_type=str)
    model       = Field(field_type=str)
