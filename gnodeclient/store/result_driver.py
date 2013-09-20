"""
This module defines so called result driver classes. A result driver is used
in order to generate ready to use result objects from objects returned by a
store.
"""

import quantities as pq

from odml import Section, Property, Value
from neo import Block, Segment, EventArray, Event, EpochArray, Epoch, RecordingChannelGroup, RecordingChannel, \
    Unit, SpikeTrain, Spike, AnalogSignalArray, AnalogSignal, IrregularlySampledSignal

from peak.util.proxies import LazyProxy

from gnodeclient.model.rest_model import Models, RestResult
from gnodeclient.store.proxies import lazy_list_loader, lazy_value_loader


class ResultDriver(object):

    def __init__(self, store):
        self.__store = store

    #
    # Properties
    #

    @property
    def store(self):
        return self.__store

    #
    # Methods
    #

    def to_result(self, obj):
        raise NotImplementedError()

    def to_model(self, native):
        raise NotImplementedError()


class NativeDriver(ResultDriver):

    MODEL_MAP = {
        #Models.DATAFILE: "datafile",
        Models.SECTION: Section,
        Models.PROPERTY: Property,
        Models.VALUE: Value,
        Models.BLOCK: Block,
        Models.SEGMENT: Segment,
        Models.EVENTARRAY: EventArray,
        Models.EVENT: Event,
        Models.EPOCHARRAY: EpochArray,
        Models.EPOCH: Epoch,
        Models.RECORDINGCHANNELGROUP: RecordingChannelGroup,
        Models.RECORDINGCHANNEL: RecordingChannel,
        Models.UNIT: Unit,
        Models.SPIKETRAIN: SpikeTrain,
        Models.SPIKE: Spike,
        Models.ANALOGSIGNALARRAY: AnalogSignalArray,
        Models.ANALOGSIGNAL: AnalogSignal,
        Models.IRREGULARLYSAMPLEDSIGNAL: IrregularlySampledSignal,
    }

    def to_result(self, obj):
        """
        Converts a model into a usable result.

        :param obj: The object to convert.
        :type obj: RestResult

        :returns: A native neo or odml object.
        :rtype: object
        """
        if obj.model in NativeDriver.MODEL_MAP:
            # collect kwargs for object construction
            kw = {}

            for field_name in obj.obligatory_fields:
                field = obj.get_field(field_name)
                field_val = getattr(obj, field_name)

                if field.type_info == "data":
                    kw[field_name] = pq.Quantity(field_val.data, field_val.units)

                elif field.type_info == "datafile":
                    kw[field_name] = pq.Quantity([], field_val.units)

                else:
                    kw[field_name] = field_val

            # construct object
            native = NativeDriver.MODEL_MAP[obj.model](**kw)
            setattr(native, "location", obj.location)

            # set remaining properties
            for field_name in obj.optional_fields:
                field_val = getattr(obj, field_name)
                field = obj.get_field(field_name)
                if field.is_parent:
                    if field_val is not None:
                        proxy = LazyProxy(lazy_value_loader(field_val, self.store, self))
                        setattr(native, field_name, proxy)

                elif field.is_child:
                    if field_val is not None and len(field_val) > 0:
                        proxy = LazyProxy(lazy_list_loader(field_val, self.store, self))
                        setattr(native, field_name, proxy)

                elif field.type_info == "data":
                    if field_val.data is not None and field_val.units is not None:
                        q = pq.Quantity(field_val.data, field_val.units)
                        setattr(native, field_name, q)

                elif field.type_info == "datafile":
                    # TODO handle data files
                    #print "%s: val = %s / unit = %s" % (field_name, str(field_val.data), str(field_val.units))
                    #q = pq.Quantity([], field_val.units)
                    #setattr(native, field_name, q)
                    pass

                elif hasattr(native, field_name):
                    setattr(native, field_name, field_val)

            return native

        else:
            return obj
