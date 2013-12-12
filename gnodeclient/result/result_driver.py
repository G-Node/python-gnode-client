# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
This module defines so called result driver classes. A result driver is used
in order to generate ready to use result objects from objects returned by a
store.
"""

from __future__ import print_function, absolute_import, division

import numpy
import quantities as pq

#import odml
import odml.base
import odml.section
import odml.property
import odml.value
import neo

from gnodeclient.result.adapt_odml import Section, Property, Value
from gnodeclient.result.adapt_neo import Block, Segment, EventArray, Event, EpochArray, Epoch, \
    RecordingChannelGroup, RecordingChannel, Unit, SpikeTrain, Spike, AnalogSignalArray, \
    AnalogSignal, IrregularlySampledSignal
from gnodeclient.store.caching_rest_store import CachingRestStore
from gnodeclient.util.proxy import LazyProxy, lazy_list_loader, lazy_value_loader
from gnodeclient.model.models import Model


class ResultDriver(object):
    """
    A result driver is used to convert internally used model objects into
    objects that are returned and handled by the Session class of the client
    API. The result driver is further more responsible for the creation of
    proxy objects from permalink or location stings.
    """

    def __init__(self, store):
        """
        Constructor

        :param store: A data source that is used for the creation of proxy objects.
        :type store: BasicStore
        """
        self.__store = store

    #
    # Properties
    #

    @property
    def store(self):
        """
        Readonly property for the used sore object.

        :returns: The store object, that is used by the driver.
        :rtype: CachingRestStore
        """
        return self.__store

    #
    # Methods
    #

    def to_result(self, obj):
        """
        Converts a model into some kind of usable result (with proxies for lazy loading).

        :param obj: The object to convert.
        :type obj: Model

        :returns: The converted object.
        :rtype: object
        """
        raise NotImplementedError()

    def to_model(self, obj):
        """
        Converts an object into a internally used model object.

        :param obj: The object to convert.
        :type obj: object

        :returns: A new model object.
        :rtype: Model
        """
        raise NotImplementedError()


class NativeDriver(ResultDriver):
    """
    A driver class that allows the conversion from model objects to native neo
    or odml objects.
    """

    #
    # Maps used for object conversion
    #

    FW_MAP = {
        Model.BLOCK: Block,
        Model.SEGMENT: Segment,
        Model.EVENTARRAY: EventArray,
        Model.EVENT: Event,
        Model.EPOCHARRAY: EpochArray,
        Model.EPOCH: Epoch,
        Model.RECORDINGCHANNELGROUP: RecordingChannelGroup,
        Model.RECORDINGCHANNEL: RecordingChannel,
        Model.UNIT: Unit,
        Model.SPIKETRAIN: SpikeTrain,
        Model.SPIKE: Spike,
        Model.ANALOGSIGNALARRAY: AnalogSignalArray,
        Model.ANALOGSIGNAL: AnalogSignal,
        Model.IRREGULARLYSAMPLEDSIGNAL: IrregularlySampledSignal,
        Model.SECTION: Section,
        Model.PROPERTY: Property,
        Model.VALUE: Value,
    }

    RW_MAP = {
        Model.BLOCK: neo.Block,
        Model.SEGMENT: neo.Segment,
        Model.EVENTARRAY: neo.EventArray,
        Model.EVENT: neo.Event,
        Model.EPOCHARRAY: neo.EpochArray,
        Model.EPOCH: neo.Epoch,
        Model.RECORDINGCHANNELGROUP: neo.RecordingChannelGroup,
        Model.RECORDINGCHANNEL: neo.RecordingChannel,
        Model.UNIT: neo.Unit,
        Model.SPIKETRAIN: neo.SpikeTrain,
        Model.SPIKE: neo.Spike,
        Model.ANALOGSIGNALARRAY: neo.AnalogSignalArray,
        Model.ANALOGSIGNAL: neo.AnalogSignal,
        Model.IRREGULARLYSAMPLEDSIGNAL: neo.IrregularlySampledSignal,
        Model.SECTION: odml.section.Section,
        Model.PROPERTY: odml.property.Property,
        Model.VALUE: odml.value.Value,
    }

    #
    # Methods
    #

    def to_result(self, obj):
        """
        Converts a model into a usable result.

        :param obj: The object to convert.
        :type obj: Model

        :returns: A native neo or odml object.
        :rtype: object
        """
        if obj.model in NativeDriver.FW_MAP:
            # collect kwargs for object construction
            kw = {}

            for field_name in obj.obligatory_fields:
                field = obj.get_field(field_name)
                field_val = getattr(obj, field_name)

                if field.type_info == "data":
                    kw[field_name] = pq.Quantity(field_val["data"], field_val["units"])

                elif field.type_info == "datafile":
                    units = field_val["units"]
                    data = self.store.get_array(field_val["data"])
                    if units is not None:
                        kw[field_name] = pq.Quantity(data, units)
                    else:
                        kw[field_name] = numpy.array(data)

                elif obj.model == Model.PROPERTY and field.type_info == Model.VALUE:
                    proxy = LazyProxy(lazy_list_loader(field_val, self.store, self, odml.base.SafeList))
                    kw["value"] = proxy

                else:
                    kw[field_name] = field_val

            # construct object
            native = NativeDriver.FW_MAP[obj.model](**kw)
            setattr(native, "location", obj.location)

            # set remaining properties
            for field_name in obj.optional_fields:
                field_val = getattr(obj, field_name)
                field = obj.get_field(field_name)
                if field.is_parent:
                    if field_val is not None:
                        proxy = LazyProxy(lazy_value_loader(field_val, self.store, self))
                        if obj.model == Model.VALUE and field_name == "parent":
                            setattr(native, "_property", proxy)
                        elif obj.model == Model.PROPERTY and field_name == "parent":
                            setattr(native, "_section", proxy)
                        else:
                            setattr(native, field_name, proxy)

                elif field.is_child:
                    list_cls = list
                    if field.type_info == Model.SECTION or field.type_info == Model.PROPERTY:
                        list_cls = odml.base.SmartList
                    elif field.type_info == Model.VALUE:
                        list_cls = odml.base.SafeList

                    if field_val is not None and len(field_val) > 0:
                        proxy = LazyProxy(lazy_list_loader(field_val, self.store, self, list_cls))
                        # TODO think about a better way to assign attrs
                        if field.type_info in [Model.SECTION, Model.VALUE] and field_name != "metadata":
                            setattr(native, '_' + field_name, proxy)
                        elif field.type_info == Model.PROPERTY:
                            setattr(native, '_props', proxy)
                        else:
                            setattr(native, field_name, proxy)

                elif field.type_info == "data":
                    if field_val["data"] is not None and field_val["units"] is not None:
                        q = pq.Quantity(field_val["data"], field_val["units"])
                        setattr(native, field_name, q)

                elif field.type_info == "datafile":
                    if field_val["data"] is not None and field_val["units"] is not None:
                        units = field_val["units"]
                        data = self.store.get_array(field_val["data"])
                        q = pq.Quantity(data, units)
                        setattr(native, field_name, q)

                elif hasattr(native, field_name):
                    setattr(native, field_name, field_val)

            return native

        else:
            return obj

    def to_model(self, obj):
        """
        Converts a native neo or odml object into model object.

        :param obj: The object to convert.
        :type obj: object

        :returns: A new model object.
        :rtype: Model
        """
        # TODO detect unbound (newly created and not persisted) related objects and throw an error
        # get type name and create a model
        model_obj = None
        for model_name in NativeDriver.RW_MAP:
            cls = NativeDriver.RW_MAP[model_name]

            if isinstance(obj, cls):
                model_obj = Model.create(model_name)
                break

        if model_obj is None:
            raise TypeError("The type of the native object (%s) is not a compatible type!" % type(obj))

        # iterate over fields and set them on the model
        for field_name in model_obj:
            field = model_obj.get_field(field_name)
            if field.type_info != "datafile":  # non-data fields
                if hasattr(obj, field_name):
                    field_val = getattr(obj, field_name, field.default)

                    # special treatment for the location field
                    if field_name == "location" and field_val is not None:
                        model_obj.location = field_val
                        model_obj.id = field_val.split("/")[-1]
                    # process all child relationships
                    elif field.is_child:
                        if field_val is not None:
                            locations = []
                            for val in field_val:
                                if hasattr(val, 'location'):
                                    locations.append(val.location)

                            model_obj[field_name] = locations
                    # process all parent relationships
                    elif field.is_parent:
                        if field_val is not None and hasattr(field_val, 'location'):
                            model_obj[field_name] = field_val.location
                    # data fields
                    elif field.type_info == "data":
                        if field_val is not None:
                            data = float(field_val)
                            units = field_val.dimensionality.string
                            model_obj[field_name] = {"data": data, "units": units}
                            # default
                    else:
                        if isinstance(field_val, numpy.ndarray):
                            field_val = list(field_val)
                        model_obj[field_name] = field_val

            else:  # datafile fields
                if field_name == "signal" and model_obj.model in (Model.ANALOGSIGNAL, Model.ANALOGSIGNALARRAY,
                                                                  Model.IRREGULARLYSAMPLEDSIGNAL):
                    units = obj.dimensionality.string
                    datafile_location = self.store.set_array(obj, temporary=True)
                    model_obj[field_name] = {"units": units, "data": datafile_location}
                elif field_name == "times" and model_obj.model == Model.SPIKETRAIN:
                    units = obj.dimensionality.string
                    datafile_location = self.store.set_array(obj, temporary=True)
                    model_obj[field_name] = {"units": units, "data": datafile_location}
                elif hasattr(obj, field_name):
                    field_val = getattr(obj, field_name, field.default)
                    if field_val is not None:
                        if hasattr(field_val, "dimensionality"):
                            units = field_val.dimensionality.string
                        else:
                            units = None
                        datafile_location = self.store.set_array(field_val, temporary=True)
                        model_obj[field_name] = {"units": units, "data": datafile_location}

        return model_obj
