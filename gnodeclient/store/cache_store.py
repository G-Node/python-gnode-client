# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import print_function, absolute_import, division

import os

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse

import gnodeclient.util.hdfio as hdfio
import gnodeclient.util.helper as helper
import gnodeclient.store.convert as convert
from gnodeclient.store.basic_store import BasicStore
from gnodeclient.util.cache import Cache


class CacheStore(BasicStore):
    """
    A simple cache store.
    """

    def __init__(self, location=None):
        super(CacheStore, self).__init__(location)
        self.__cache = Cache(self.location)

    def connect(self):
        if self.__cache is None:
            self.__cache = Cache(self.location)

    def is_connected(self):
        return self.__cache is not None

    def disconnect(self):
        if self.__cache is not None:
            del self.__cache
        self.__cache = None

    def get(self, location, temporary=False):
        obj = self.__cache.get(location, temporary)
        if obj is not None:
            entity = convert.collections_to_model(obj)
            return entity
        else:
            return None

    def get_file(self, location, temporary=False):
        """
        Get raw file data (bytestring) from the cache.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: str
        """
        data = self.__cache.get_file(location, temporary)
        return data

    def get_array(self, location, temporary=False):
        """
        Read array data from an hdf5 file in the cache.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: numpy.ndarray|list
        """
        ident = helper.id_from_location(location)
        path = self.__cache.file_cache_path(ident, temporary)

        if os.path.isfile(path):
            data = hdfio.read_array_data(path)
            return data
        else:
            return None

    def set(self, entity, temporary=False):
        if entity is not None:
            obj = convert.model_to_collections(entity)
            self.__cache.set(entity.location, obj, temporary)
        return entity

    def set_file(self, data, location=None, temporary=False):
        """
        Save raw file data in the cache.

        :param data: The raw data of the file.
        :type data: str
        :param location: The location of the file.
        :type location: str

        :returns: The url to the uploaded file.
        :rtype: str
        """
        if location is None:
            location = "datafiles/datafile/" + helper.random_str()

        self.__cache.set_file(location, data, temporary)

        return location

    def set_array(self, array_data, location=None, temporary=False):
        """
        Save array data in a cached HDF5 file.

        :param array_data: The raw data to store.
        :type array_data: numpy.ndarray|list
        :param location: The location of the file.
        :type location: str

        :returns: The url to the uploaded file.
        :rtype: str
        """
        if location is None:
            ident = helper.random_str()
            location = "datafiles/datafile/" + ident
        else:
            ident = helper.id_from_location(location)

        path = self.__cache.file_cache_path(ident, temporary)
        hdfio.store_array_data(path, array_data)

        return location

    def delete(self, entity, temporary=False):
        if entity is not None:
            self.__cache.delete(entity.location, temporary)

    def delete_file(self, location, temporary=False):
        self.__cache.delete_file(location, temporary)

    def clear_cache(self, temporary=False):
        self.__cache.clear(temporary)
