# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import print_function, absolute_import, division

from numbers import Number
from gnodeclient.util.declarative_models import Field


class FTyped(Field):
    """
    A field class that performs type checks.
    """

    def check(self, val):
        if self.field_type is not None:
            return isinstance(val, self.field_type)
        elif self.obligatory:
            return False
        else:
            return True


class FNumber(Field):
    """
    A special field class for number values.
    """

    def __init__(self, ignore=False, type_info="number", default=None, obligatory=False,
                 min_val=None, max_val=None, name_mapping=None):
        super(FNumber, self).__init__(False, False, ignore, Number, type_info, default, obligatory, name_mapping)
        self.__min = min_val
        self.__max = max_val

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


class FQuantity(Field):
    """
    A special field class for quantities. In this case a quantity is everything that acts like
    a dict that has the keys "units" and "data".
    """

    def __init__(self, ignore=False, default=None, obligatory=False, name_mapping=None):
        super(FQuantity, self).__init__(False, False, ignore, dict, "data", default, obligatory, name_mapping)

    def check(self, val):
        check_passed = True
        if val is not None:
            try:
                data = val["data"]
                if data is not None and not isinstance(data, Number):
                    check_passed = False
                units = val["units"]
                if units is not None and not isinstance(units, str):
                    check_passed = False
            except RuntimeError:
                check_passed = False

        return check_passed


class FDatafile(Field):
    """
    A special field class for data files. A data file is everything that acts like
    a dict that has the keys "units" and "data".
    """

    def __init__(self, ignore=False, default=None, obligatory=False, name_mapping=False):
        super(FDatafile, self).__init__(False, False, ignore, dict, "datafile", default, obligatory, name_mapping)

    def check(self, val):
        check_passed = True
        if val is not None:
            try:
                _ = val["data"]
                units = val["units"]
                if units is not None and not isinstance(units, str):
                    check_passed = False
            except RuntimeError:
                check_passed = False

        return check_passed


class FParent(FTyped):
    """
    A special field class for parent relationships.
    """

    def __init__(self, ignore=False, field_type=object, type_info=None, default=None,
                 obligatory=False, name_mapping=None):
        super(FParent, self).__init__(True, False, ignore, field_type, type_info, default, obligatory, name_mapping)


class FChildren(FTyped):
    """
    A special field class for child relationships.
    """

    def __init__(self, ignore=False, type_info=None, obligatory=False, name_mapping=None):
        super(FChildren, self).__init__(False, True, ignore, list, type_info, [], obligatory, name_mapping)
