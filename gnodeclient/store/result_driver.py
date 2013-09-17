"""
This module defines so called result driver classes. A result driver is used
in order to generate ready to use result objects from objects returned by a
store.
"""
import quantities as pq
from neo import Segment, AnalogSignal
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


class NativeDriver(ResultDriver):

    MODEL_MAP = {
        Models.ANALOGSIGNAL: AnalogSignal,
        Models.SEGMENT: Segment
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

            native = NativeDriver.MODEL_MAP[obj.model](**kw)

            for field_name in obj.optional_fields:
                field = obj.get_field(field_name)
                if field.is_parent:
                    field_val = getattr(obj, field_name)

                    if field_val is not None:
                        proxy = LazyProxy(lazy_value_loader(field_val, self.store, self))
                        #proxy = ProxyPropValue(field_name, str(field_val), self.store, self)
                        setattr(native, field_name, proxy)

                elif field.is_child:
                    field_val = getattr(obj, field_name)

                    if field_val is not None and len(field_val) > 0:
                        proxy = LazyProxy(lazy_list_loader(field_val, self.store, self))
                        #proxy = ProxyPropValueList(field_name, field_val, self.store, self)
                        setattr(native, field_name, proxy)

                elif field.type_info == "data":
                    field_val = getattr(obj, field_name)
                    q = pq.Quantity(field_val.data, field_val.units)
                    setattr(native, field_name, q)

                elif field.type_info == "datafile":
                    field_val = getattr(obj, field_name)
                    q = pq.Quantity([], field_val.units)
                    setattr(native, field_name, q)

            return native

        else:
            return obj
