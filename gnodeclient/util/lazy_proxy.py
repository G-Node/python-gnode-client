__author__ = 'adrian'

_NAMES = [
    '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
    '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
    '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
    '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
    '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
    '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
    '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
    '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
    '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
    '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
    '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
    '__truediv__', '__xor__'
]


def _proxy_load(self):
    if self._cache is None:
        self._cache = self._func()
    return self._cache


def _proxy_getattribute(self, attr, oga=object.__getattribute__):
    subject = oga(self,"_value")
    if attr=="_value":
        return subject
    return getattr(subject,attr)


def _proxy_setattr(self,attr,val, osa=object.__setattr__):
    if attr=="_value":
        osa(self,attr,val)
    else:
        setattr(self.__subject__,attr,val)


def _proxy_delattr(self,attr, oda=object.__delattr__):
    if attr=="_value":
        oda(self,attr)
    else:
        delattr(self.__subject__,attr)


def _make_proxy_method(method_name):
    def proxy_method(self, *args, **kwargs):
        return getattr(object.__getattribute__(self, "_value"), method_name)(*args, **kwargs)
    return proxy_method


class LazyProxyMeta(type):

    def __new__(mcs, name, bases, dct):

        dct["_cache"] = None
        dct["_value"] = property(_proxy_load)

        for method_name in _NAMES:
            dct[method_name] = _make_proxy_method(method_name)

        return type.__new__(mcs, name, bases, dct)


class LazyProxy(object):

    __metaclass__ = LazyProxyMeta

    def __init__(self, func):
        self._func = func
