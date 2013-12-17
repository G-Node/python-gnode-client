# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
This module provides some classes that can be used as mixins for native result classes e.g.
neo and odml types.
"""


class WithLocation(object):

    @property
    def location(self):
        try:
            return self.__location
        except AttributeError:
            self.__location = None
            return self.__location

    @location.setter
    def location(self, location):
        self.__location = location

    @location.deleter
    def location(self):
        self.__location = None


class WithMetadata(object):

    @property
    def metadata(self):
        try:
            return self.__metadata
        except AttributeError:
            self.__metadata = None
            return self.__metadata

    @metadata.setter
    def metadata(self, metadata):
        self.__metadata = metadata

    @metadata.deleter
    def metadata(self):
        self.__metadata = None


class WithSection(object):

    @property
    def section(self):
        try:
            return self.__section
        except AttributeError:
            self.__section = None
            return self.__section

    @section.setter
    def section(self, section):
        self.__section = section

    @section.deleter
    def section(self):
        self.__section = None


class WithBlock(object):

    @property
    def blocks(self):
        try:
            return self.__blocks
        except AttributeError:
            self.__blocks = []
            return self.__blocks

    @blocks.setter
    def blocks(self, block):
        self.__blocks = block

    @blocks.deleter
    def blocks(self):
        self.__blocks = None
