"""
The module provides an implementation of a lazy loading proxy class
"""

# Some names to create generic proxy methods for
_NAMES = [
    "__abs__", "__add__", "__and__", "__call__", "__cmp__", "__coerce__",
    "__contains__", "__delitem__", "__delslice__", "__div__", "__divmod__",
    "__eq__", "__float__", "__floordiv__", "__ge__", "__getitem__",
    "__getslice__", "__gt__", "__hash__", "__hex__", "__iadd__", "__iand__",
    "__idiv__", "__idivmod__", "__ifloordiv__", "__ilshift__", "__imod__",
    "__imul__", "__int__", "__invert__", "__ior__", "__ipow__", "__irshift__",
    "__isub__", "__iter__", "__itruediv__", "__ixor__", "__le__", "__len__",
    "__long__", "__lshift__", "__lt__", "__mod__", "__mul__", "__ne__",
    "__neg__", "__oct__", "__or__", "__pos__", "__pow__", "__radd__",
    "__rand__", "__rdiv__", "__rdivmod__", "__reduce__", "__reduce_ex__",
    "__repr__", "__reversed__", "__rfloorfiv__", "__rlshift__", "__rmod__",
    "__rmul__", "__ror__", "__rpow__", "__rrshift__", "__rshift__", "__rsub__",
    "__rtruediv__", "__rxor__", "__setitem__", "__setslice__", "__sub__",
    "__truediv__", "__xor__", "next"
]

# Some names the proxy uses internally
_PROXY_NAMES = [
    "_value", "_loader", "_cache"
]


def _proxy_load(self):
    """
    A function that executes the lazy load. It is used to create a read only property.
    """
    if self._cache is None:
        self._cache = self._loader()
    return self._cache


def _proxy_getattribute(self, attr, oga=object.__getattribute__):
    """
    The implementation of __getattribute__ of the proxy.
    """
    if attr in _PROXY_NAMES:
        return oga(self, attr)
    else:
        subject = oga(self, "_value")
        return getattr(subject, attr)


def _proxy_setattr(self, attr, val, osa=object.__setattr__):
    """
    The implementation of __setattr__ of the proxy.
    """
    if attr in _PROXY_NAMES:
        osa(self, attr, val)
    else:
        setattr(self._value, attr, val)


def _proxy_delattr(self, attr, oda=object.__delattr__):
    """
    The implementation of __delattr__ of the proxy.
    """
    if attr in _PROXY_NAMES:
        oda(self, attr)
    else:
        delattr(self._value, attr)


def _make_proxy_method(method_name):
    """
    Factory for generic proxy methods.
    """
    def proxy_method(self, *args, **kwargs):
        return getattr(object.__getattribute__(self, "_value"), method_name)(*args, **kwargs)
    return proxy_method


class LazyProxyMeta(type):
    """
    A meta class that adds important proxy methods to another class. A lazy proxy class defines three
    own attributes.
    """

    def __new__(mcs, name, bases, dct):

        dct["_cache"] = None
        dct["_value"] = property(_proxy_load)

        for method_name in _NAMES:
            dct[method_name] = _make_proxy_method(method_name)

        dct["__getattribute__"] = _proxy_getattribute
        dct["__setattr__"] = _proxy_setattr
        dct["__delattr__"] = _proxy_delattr

        return type.__new__(mcs, name, bases, dct)


class LazyProxy(object):
    """
    A lazy loading proxy class.
    """

    __metaclass__ = LazyProxyMeta

    def __init__(self, loader):
        """
        Initialize the proxy class. As a first parameter the constructor expects a
        function. When the proxy is accessed for the first time the function is invoked
        without parameters, its return value is the object that is actually managed by
        the proxy.

        :param loader: The function that is called in order to load the value of the proxy.
        :type loader: function
        """
        self._loader = loader


def lazy_value_loader(location, store, result_driver):

    def do_lazy_load():

        if isinstance(location, list) and len(location) == 1:
            loc = location[0]
        else:
            loc = location

        obj = store.get(loc, False)
        res = result_driver.to_result(obj)
        return res

    return do_lazy_load


def lazy_list_loader(locations, store, result_driver, list_cls):

    def do_lazy_load():
        results = list_cls()

        for location in locations:
            obj = store.get(location, False)
            res = result_driver.to_result(obj)
            results.append(res)

        return results

    return do_lazy_load