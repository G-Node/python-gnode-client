# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from odml.section import BaseSection
from odml.property import BaseProperty
from odml.value import BaseValue
from gnodeclient.result.adapt_mixins import WithLocation, WithBlock


class Section(WithLocation, WithBlock, BaseSection):
    pass


class Property(WithLocation, BaseProperty):
    pass


class Value(WithLocation, BaseValue):
    pass
