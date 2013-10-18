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
