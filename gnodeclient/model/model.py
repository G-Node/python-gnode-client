"""
This module provides some classes for the definitions of models and their fields. The main idea behind
this kind of model classes is the ability to inspect certain properties of fields during runtime
and to find an manipulate fields that fulfill specific criteria (e.g get all values form all mandatory
fields).

Example model class:
>>> class Foo(Model):
>>>     name = Field(default="foo", optional=False, type=str)

Create object and set/get values:
>>> foo = Foo()
>>> foo.name = "bar"
>>> some_name = foo['name']

Inspect the field
>>> descriptor = foo.get_field('name')
>>> if not descriptor.optional
>>>     print "name is not optional"
"""

from weakref import WeakKeyDictionary


class FieldDescriptor(object):
    """
    Provides additional information about a certain field.
    """

    def __init__(self, optional=True, is_parent=False, is_child=False, default=None,
                 type=object, type_info=None):
        """
        Constructor for FieldDescriptor.

        :param optional: Specifies if a field is optional or obligatory.
        :type optional: bool

        :param is_parent: Defines a field as a parent relationship (one/many to one).
        :type is_parent: bool

        :param is_child: Defines a field as a child relationship (one to many)
        :type is_child: bool

        :param default: The default value of a field.
        :type default: object

        :param type: The type of the value of the field.
        :type type: class

        :param type_info: Some additional information about the type of the value e.g. a string.
        :type type_info: object
        """
        self.__optional = optional
        self.__is_parent = is_parent
        self.__is_child = is_child
        self.__default = default
        self.__type = type
        self.__type_info = type_info

    @property
    def optional(self):
        """Specifies if a field is optional or obligatory."""
        return self.__optional

    @property
    def is_parent(self):
        """Defines a field as a parent relationship (one/many to one)."""
        return self.__is_parent

    @property
    def is_child(self):
        """Defines a field as a child relationship (one to many)"""
        return self.__is_child

    @property
    def default(self):
        """The default value of a field."""
        return self.__default

    @property
    def type(self):
        """The type of the value of the field."""
        return self.__type

    @property
    def type_info(self):
        """Some additional information about the type of the value e.g. a string."""
        return self.__type_info

    #
    # Built-in functions
    #

    def __repr__(self):
        return str(self)

    def __str__(self):
        template = "{optional: %s, is_parent: %s, is_child: %s, default: %s, type: %s, type_info: %s}"
        return template % (self.optional, self.is_parent, self.is_child, self.default, self.type, self.type_info)


class Field(object):
    """
    A field of a class, that manages the access and behaviour of its value.
    """

    def __init__(self, optional=True, is_parent=False, is_child=False, default=None, type=object, type_info=None):
        """
        Constructor for FieldDescriptor.

        :param optional: Specifies if a field is optional or obligatory.
        :type optional: bool

        :param is_parent: Defines a field as a parent relationship (one/many to one).
        :type is_parent: bool

        :param is_child: Defines a field as a child relationship (one to many)
        :type is_child: bool

        :param default: The default value of a field.
        :type default: object

        :param type: The type of the value of the field.
        :type type: class

        :param type_info: Some additional information about the type of the value e.g. a string.
        :type type_info: object
        """
        self.__values = WeakKeyDictionary()
        self.__desc = FieldDescriptor(optional=optional, is_parent=is_parent, is_child=is_child, default=default,
                                      type=type, type_info=type_info)

    @property
    def desc(self):
        """The field descriptor of the field."""
        return self.__desc

    def check(self, value):
        """
        A method that is always called if a new value is applied in order to check if
        this value is valid.

        :param value: The value to check.
        :type value: object

        :return: True if the value is valid, False otherwise.
        """
        return True

    #
    # Built-in functions
    #

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.__values.get(instance, self.desc.default)

    def __set__(self, instance, value):
        if not self.check(value):
            raise ValueError("Unable to set value due to failed check: value was %s" % value)

        if value is None:
            self.__values[instance] = self.desc.default
        else:
            self.__values[instance] = value

    def __delete__(self, instance):
        del self.__values[instance]
        self.__values[instance] = self.desc.default


class Model(object):
    """
    A model that can serve as a base class for objects that make use of the Field class
    in order to define their properties. It provides methods that makes it easier to inspect
    the field descriptors at runtime. All fields can be accessed as a property or like an
    item of a map.
    """

    def __init__(self, *args, **kwargs):
        """
        Generic init method that initiates all fields
        """
        allattr = dir(self.__class__)
        for name in kwargs:
            if name in allattr:
                field = getattr(self.__class__, name)
                if isinstance(field, Field):
                    setattr(self, name, kwargs[name])

    def get_fields(self, field_filter=lambda x: True):
        """
        Get field descriptors from all fields.

        :param field_filter: An optional filter that is applied on every field descriptor.
        :type field_filter: function

        :return: A dict of all field descriptors accessible by their field name.
        """
        descriptors = {}

        allattr = dir(self.__class__)
        for name in allattr:
            field = getattr(self.__class__, name)
            if isinstance(field, Field) and field_filter(field.desc):
                descriptors[name] = field.desc

        return descriptors

    @property
    def fields(self):
        """Descriptors for all fields of the model"""
        return self.get_fields()

    @property
    def parent_fields(self):
        """Descriptors for all fields of the model, that are parent relationships"""
        return self.get_fields(lambda f: f.is_parent)

    @property
    def child_fields(self):
        """Descriptors for all fields of the model, that are child relationships"""
        return self.get_fields(lambda f: f.is_child)

    @property
    def reference_fields(self):
        """Descriptors for all fields of the model, that are some kind of relationship"""
        return self.get_fields(lambda f: f.is_parent or f.is_child)

    @property
    def none_reference_fields(self):
        """Descriptors for all fields of the model, that are not a kind of relationship"""
        return self.get_fields(lambda f: not f.is_parent and not f.is_child)

    @property
    def optional_fields(self):
        """Descriptors for all fields of the model, that are optional"""
        return self.get_fields(lambda f: f.optional)

    @property
    def obligatory_fields(self):
        """Descriptors for all fields of the model, that are obligatory"""
        return self.get_fields(lambda f: not f.optional)

    def get_field(self, name):
        """
        Get a field descriptor by the name of the field.

        :param name: The name of the field.
        :type name: str

        :return: The field descriptor or None if the field does not exits.
        """
        descriptor = None

        if hasattr(self.__class__, name):
            field = getattr(self.__class__, name)
            if isinstance(field, Field):
                descriptor = field.desc

        return descriptor

    #
    # Built-in functions
    #

    def __getitem__(self, name):
        if hasattr(self.__class__, name):
            field = getattr(self.__class__, name)
            if isinstance(field, Field):
                return getattr(self, name)
            else:
                raise KeyError("Model has no such field: %s" % name)

    def __setitem__(self, name, value):
        if hasattr(self.__class__, name):
            field = getattr(self.__class__, name)
            if isinstance(field, Field):
                return setattr(self, name, value)
            else:
                raise KeyError("Model has no such field: %s" % name)

    def __len__(self):
        return len(self.get_fields())

    def __iter__(self):
        return iter(self.get_fields())

    def __str__(self):
        template = "<%s: %s>"
        kv_str = ""
        fields = self.fields
        for name in fields:
            kv_str += "%s=%s, " % (name, getattr(self, name))
        if len(fields) > 0:
            kv_str = kv_str[:len(kv_str) - 2]
        return template % (self.__class__.__name__, kv_str)

    def __repr__(self):
        return str(self)
