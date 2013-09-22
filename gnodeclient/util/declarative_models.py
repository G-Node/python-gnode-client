"""
This module provides an implementation for semi declarative model definitions in python. Models are
defined by classes inheriting from the Model base class. Properties of models are defined by assigning
instances of the Field class to fields of the model class.

Example model class:
>>> class Foo(Model):
>>>     name = Field(default="foo", obligatory=True, type=str)

Create object and set/get values:
>>> foo = Foo()
>>> foo.name = "bar"
>>> foo["name"] = "bar"     # same as above
>>> some_name = foo.name
>>> some_name = foo["name"] # same as above
>>> del foo.name            # del sets default if provided

Inspection of fields
>>> field = foo.inspect_field('name')
>>> if field.obligatory
>>>     print "name is not optional"
"""
from numbers import Number

# import * guard
__all__ = ("Field", "Model", "FTyped", "FNumber")

# some constants
_REGISTERED_FIELDS = "__registered_fields"      # the field where field descriptors are stored
_REGISTERED_FIELDS_GETTER = "inspect_fields"    # readonly property for field descriptors access


def _mangle_field_name(cls_name, field_name):
    """
    Generate mangled names.
    """
    return "_%s__%s" % (cls_name, field_name)


def _generate_field_property(dct, fields):
    """
    Generates a property that returns all registered fields.
    """
    field_name = _REGISTERED_FIELDS

    def getter(self):
        return getattr(self, field_name)

    dct[field_name] = fields
    dct[_REGISTERED_FIELDS_GETTER] = property(getter, None, None, "All registered field descriptors")


class Field(object):
    """
    Field objects can be used to describe fields/properties of model classes.
    """

    def __init__(self, is_parent=False, is_child=False, ignore=False, field_type=object, type_info=None,
                 default=None, obligatory=False):
        self.__is_parent = is_parent
        self.__is_child = is_child
        self.__ignore = ignore
        self.__field_type = field_type
        self.__type_info = type_info
        self.__default = default
        self.__obligatory = obligatory

    #
    # Properties
    #

    @property
    def is_parent(self):
        return self.__is_parent

    @property
    def is_child(self):
        return self.__is_child

    @property
    def ignore(self):
        return self.__ignore

    @property
    def field_type(self):
        return self.__field_type

    @property
    def type_info(self):
        return self.__type_info

    @property
    def default(self):
        return self.__default

    @property
    def obligatory(self):
        return self.__obligatory

    #
    # Methods
    #

    def check(self, val):
        return True

    def generate_property(self, dct, cls_name, field_name, doc=""):
        mangled_name = _mangle_field_name(cls_name, field_name)

        def getter(myself):
            if not hasattr(myself, mangled_name):
                setattr(myself, mangled_name, self.default)
            return getattr(myself, mangled_name)

        def setter(myself, value):
            if self.check(value):
                setattr(myself, mangled_name, value)
            else:
                raise ValueError("Not a valid value: %s!" % str(value))

        def deleter(myself):
            if hasattr(myself, mangled_name):
                delattr(myself, mangled_name)
            if self.default is not None:
                setattr(myself, mangled_name, self.default)

        dct[field_name] = property(getter, setter, deleter, doc)

    #
    # Built-in functions
    #

    def __repr__(self):
        return str(self)

    def __str__(self):
        template = "{is_parent: %s, is_child: %s, default: %s, field_type: %s, type_info: %s, obligatory: %s}"
        return template % (self.is_parent, self.is_child, self.default, self.field_type, self.type_info,
                           self.obligatory)


class FTyped(Field):
    """
    A field class that performs type checks.
    """

    def check(self, val):
        if self.field_type is not None:
            return isinstance(val, self.field_type)
        else:
            return True


class FNumber(Field):
    """
    A special field class for number values.
    """

    def __init__(self, ignore=False, field_type=Number, type_info="number", default=None, obligatory=False,
                 min=None, max=None):
        super(FNumber, self).__init__(False, False, ignore, field_type, type_info, default, obligatory)
        self.__min = min
        self.__max = max

    #
    # Properties
    #

    @property
    def min(self):
        return self.__min

    @property
    def max(self):
        return self.__max

    #
    # Methods
    #

    def check(self, val):
        passed = True
        if self.field_type is not None:
            passed = isinstance(val, self.field_type)
        if self.min is not None and val < self.min:
            passed = False
        if self.max is not None and val > self.max:
            passed = False
        return passed


class ModelMeta(type):
    """
    A meta class for the creation of model classes.
    """

    def __new__(mcs, name, bases, dct):

        fields = {}

        # collect field descriptors from base classes
        for b in bases:
            if hasattr(b, _REGISTERED_FIELDS):
                fields.update(getattr(b, _REGISTERED_FIELDS))

        # collect field descriptors from own dict
        for f in dct.keys():
            f_desc = dct[f]
            if isinstance(f_desc, Field):
                f_desc.generate_property(dct, name, f, "Property accessor for %s" % f)
                fields[f] = f_desc

        _generate_field_property(dct, fields)
        return type.__new__(mcs, name, bases, dct)


class Model(object):

    __metaclass__ = ModelMeta  # This is key feature of the model class

    def __init__(self, *args, **kwargs):
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        for f_name in fields:
            if f_name in kwargs:
                setattr(self, f_name, kwargs[f_name])

    #
    # Properties
    #

    @property
    def inspect_parents(self):
        return self.__inspect_filtered(lambda x: x.is_parent)

    @property
    def inspect_children(self):
        return self.__inspect_filtered(lambda x: x.is_child)

    @property
    def inspect_relationship(self):
        return self.__inspect_filtered(lambda x: x.is_child or x.is_parent)

    @property
    def inspect_non_relationship(self):
        return self.__inspect_filtered(lambda x: not x.is_child and not x.is_parent)

    @property
    def inspect_optional(self):
        return self.__inspect_filtered(lambda x: not x.obligatory)

    @property
    def inspect_obligatory(self):
        return self.__inspect_filtered(lambda x: x.obligatory)

    @property
    def inspect_obligatory(self):
        return self.__inspect_filtered(lambda x: x.obligatory)

    #
    # Methods
    #

    def inspect_field(self, name):
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        if name in fields:
            return fields[name]
        else:
            return None

    def __inspect_filtered(self, filter=lambda x: True):
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        filtered_fields = {}

        for f_name in fields:
            f_desc = fields[f_name]
            if filter(f_desc):
                filtered_fields[f_name] = f_desc

        return filtered_fields

    #
    # Built-in functions
    #

    def __getitem__(self, name):
        field = self.inspect_field(name)
        if field is not None:
            return getattr(self, name)
        else:
            raise KeyError("Model has no such field: %s" % name)

    def __setitem__(self, name, value):
        field = self.inspect_field(name)
        if field is not None:
            setattr(self, name, value)
        else:
            raise KeyError("Model has no such field: %s" % name)

    def __len__(self):
        return len(getattr(self, _REGISTERED_FIELDS_GETTER))

    def __iter__(self):
        return iter(getattr(self, _REGISTERED_FIELDS_GETTER))

    def __str__(self):
        template = "<%s: %s>"
        kv_str = ""
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        for name in fields:
            kv_str += "%s=%s, " % (name, getattr(self, name))
        if len(fields) > 0:
            kv_str = kv_str[:len(kv_str) - 2]
        return template % (self.__class__.__name__, kv_str)

    def __repr__(self):
        return str(self)


class Test(Model):
    foo = Field(is_parent=True, type_info="foo")
    bar = Field(is_child=True, type_info="bar")


class Test2(Test):
    fasel = Field(is_parent=True, type_info="fasel", default="default fasel")


class Test3(Test2):
    count = FNumber(min=0, max=3, default=0)
