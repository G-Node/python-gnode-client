from __future__ import print_function, absolute_import, division

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse

import gnodeclient.store.convert as convert
from gnodeclient.store.basic_store import BasicStore
from gnodeclient.util.cache import Cache


class CacheStore(BasicStore):
    """
    A simple cache store.
    """

    def __init__(self, location=None):
        super(CacheStore, self).__init__(location)
        self.__cache = None

    def connect(self):
        self.__cache = Cache(self.location)

    def is_connected(self):
        return self.__cache is not None

    def disconnect(self):
        del self.__cache
        self.__cache = None

    def get(self, location):
        obj = self.__cache.get(location)
        if obj is not None:
            entity = convert.collections_to_model(obj)
            return entity
        else:
            return None

    def set(self, entity):
        if entity is not None:
            obj = convert.model_to_collections(entity)
            self.__cache.set(entity.location, obj)
        return entity

    def delete(self, entity):
        if entity is not None:
            self.__cache.delete(entity.location)

    def clear_cache(self):
        self.__cache.clear()
