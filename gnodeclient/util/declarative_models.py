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
>>> field = foo.get_field('name')
>>> if field.obligatory
>>>     print("name is not optional")
"""

from __future__ import print_function, absolute_import, division

# some constants
_REGISTERED_FIELDS = "__registered_fields"      # the field where field descriptors are stored
_REGISTERED_FIELDS_GETTER = "inspect_fields"    # readonly property for field descriptors access


def _mangle_field_name(cls_name, field_name):
    """
    Generate mangled names.
    """
    return "_%s__%s" % (cls_name, field_name)


def _make_registered_fields_property(dct, fields):
    """
    Generates a property that returns all registered fields.
    """
    field_name = _REGISTERED_FIELDS

    def getter(self):
        return getattr(self, field_name)

    dct[field_name] = fields
    dct[_REGISTERED_FIELDS_GETTER] = property(getter, None, None, "All registered field descriptors")


def _add_field_property_to_dct(dct, cls_name, field, field_name):
    """
    Creates a property with setter, getter and deleter from a given field, and
    adds this field to a dict.
    """
    mangled_name = _mangle_field_name(cls_name, field_name)

    def getter(myself):
        if not hasattr(myself, mangled_name):
            setattr(myself, mangled_name, field.default)
        return getattr(myself, mangled_name)

    def setter(myself, value):
        if field.check(value):
            setattr(myself, mangled_name, value)
        else:
            raise ValueError("Not a valid value: %s!" % str(value))

    def deleter(myself):
        if hasattr(myself, mangled_name):
            delattr(myself, mangled_name)
        if field.default is not None:
            setattr(myself, mangled_name, field.default)

    dct[field_name] = property(getter, setter, deleter, "Property accessor for %s.%s" % (cls_name, field_name))


class Field(object):
    """
    Field objects can be used to describe fields/properties of model classes.
    """

    def __init__(self, is_parent=False, is_child=False, ignore=False, field_type=object, type_info=None,
                 default=None, obligatory=False, name_mapping=None):
        """
        Constructor for Field.

        :param is_parent: Defines a field as a parent relationship (one/many to one).
        :type is_parent: bool

        :param is_child: Defines a field as a child relationship (one to many)
        :type is_child: bool

        :param ignore: If True the field is ignored for serialisation.
        :type ignore: bool

        :param default: The default value of a field.
        :type default: object

        :param field_type: The type of the value of the field.
        :type field_type: class

        :param type_info: Some additional information about the type of the value e.g. a string.
        :type type_info: object

        :param obligatory: Specifies if a field is optional or obligatory.
        :type obligatory: bool

        :param name_mapping: The original field name should be mapped to another name for serialisation.
        :type name_mapping: str
        """
        self.__is_parent = is_parent
        self.__is_child = is_child
        self.__ignore = ignore
        self.__field_type = field_type
        self.__type_info = type_info
        self.__default = default
        self.__obligatory = obligatory
        self.__name_mapping = name_mapping

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

    @property
    def name_mapping(self):
        return self.__name_mapping

    #
    # Methods
    #

    def check(self, val):
        return True

    #
    # Built-in functions
    #

    def __repr__(self):
        return str(self)

    def __str__(self):
        template = "{is_parent: %s, is_child: %s, default: %s, field_type: %s, type_info: %s, obligatory: %s}"
        return template % (self.is_parent, self.is_child, self.default, self.field_type, self.type_info,
                           self.obligatory)


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
        for field_name in dct.keys():
            field = dct[field_name]
            if isinstance(field, Field):
                _add_field_property_to_dct(dct, name, field, field_name)
                fields[field_name] = field

        _make_registered_fields_property(dct, fields)
        return type.__new__(mcs, name, bases, dct)


class Model(object):
    """
    A model that can serve as a base class for objects that make use of the Field class
    in order to define their properties. It provides methods that makes it easier to inspect
    the field descriptors at runtime. All fields can be accessed as a property or like an
    item of a map.
    """

    __metaclass__ = ModelMeta  # This is key feature of the model class

    def __init__(self, *args, **kwargs):
        """
        Generic init method that initiates all fields
        """
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)

        if len(args) > 0:
            raise KeyError("%s: Unable to apply non keyword arguments" % (type(self)))

        for f_name in kwargs:
            if f_name in fields:
                setattr(self, f_name, kwargs[f_name])
            else:
                raise KeyError("%s has no such field: %s" % (type(self), f_name))

    #
    # Properties
    #

    @property
    def fields(self):
        """Descriptors for all fields of the model"""
        return self.__inspect_filtered()

    @property
    def parent_fields(self):
        """Descriptors for all fields of the model, that are parent relationships"""
        return self.__inspect_filtered(lambda x: x.is_parent)

    @property
    def child_fields(self):
        """Descriptors for all fields of the model, that are child relationships"""
        return self.__inspect_filtered(lambda x: x.is_child)

    @property
    def reference_fields(self):
        """Descriptors for all fields of the model, that are some kind of relationship"""
        return self.__inspect_filtered(lambda x: x.is_child or x.is_parent)

    @property
    def none_reference_fields(self):
        """Descriptors for all fields of the model, that are not a kind of relationship"""
        return self.__inspect_filtered(lambda x: not x.is_child and not x.is_parent)

    @property
    def optional_fields(self):
        """Descriptors for all fields of the model, that are optional"""
        return self.__inspect_filtered(lambda x: not x.obligatory)

    @property
    def obligatory_fields(self):
        """Descriptors for all fields of the model, that are obligatory"""
        return self.__inspect_filtered(lambda x: x.obligatory)

    #
    # Methods
    #

    def get_field(self, name):
        """
        Get a field descriptor by the name of the field.

        :param name: The name of the field.
        :type name: str

        :return: The field descriptor or None if the field does not exits.
        :rtype: Field
        """
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        if name in fields:
            return fields[name]
        else:
            return None

    def __inspect_filtered(self, selector=lambda x: True):
        fields = getattr(self, _REGISTERED_FIELDS_GETTER)
        filtered_fields = {}

        for f_name in fields:
            f_desc = fields[f_name]
            if selector(f_desc):
                filtered_fields[f_name] = f_desc

        return filtered_fields

    #
    # Built-in functions
    #

    def __getitem__(self, name):
        field = self.get_field(name)
        if field is not None:
            return getattr(self, name)
        else:
            raise KeyError("Model has no such field: %s" % name)

    def __setitem__(self, name, value):
        field = self.get_field(name)
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
