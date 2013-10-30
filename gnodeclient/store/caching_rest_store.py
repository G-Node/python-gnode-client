# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import print_function, absolute_import, division

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse

from gnodeclient.model.models import Model
from gnodeclient.store.basic_store import BasicStore
from gnodeclient.store.cache_store import CacheStore
from gnodeclient.store.rest_store import RestStore


class CachingRestStore(BasicStore):
    """
    A store implementation, that uses an instance of BasicStore and CacheStore to implement
    an interface to the G-Node REST API with transparent caching of results. Further more it provides
    a recursive get method, which ensures the presence of all descendants of a certain entity in the cache.
    """

    def __init__(self, location, user, password, cache_location=None):
        """
        Constructor.

        :param location: The location from where the data should be accessed.
        :type location: str
        :param user: The user name (might be ignored by some kinds of store)
        :type user: str
        :param password: The password (might be ignored by some kinds of store)
        :type password: str
        :param cache_location: The location of the cache, if not set a suitable system specific default
                               will be chosen.
        :type cache_location: str
        """
        super(CachingRestStore, self).__init__(location, user, password)

        self.__cache_location = cache_location
        self.__rest_store = RestStore(location, user, password)
        self.__cache_store = CacheStore(cache_location)

    #
    # Properties
    #

    @property
    def cache_location(self):
        return self.__cache_location

    @property
    def rest_store(self):
        return self.__rest_store

    @property
    def cache_store(self):
        return self.__cache_store

    #
    # Methods
    #

    def connect(self):
        """
        Connect to the G-Node REST API and initialize a cache.
        """
        self.rest_store.connect()
        self.cache_store.connect()

    def is_connected(self):
        """
        Check the connection and the presence of a cache.
        """
        return self.rest_store.is_connected() and self.cache_store.is_connected()

    def disconnect(self):
        """
        Disconnect from the G-Node REST API and flush the cache.
        """
        self.rest_store.disconnect()
        self.cache_store.disconnect()

    def select(self, model_name, raw_filters=None):
        """
        Select data from a certain type e.g. blocks or spiketrains from the G-Node REST API
        and convert the results to a list of model objects. The results can be filtered on
        the server, by passing a dictionary of filters as second argument.

        Example:
        >>> store = CachingRestStore("http://example.com", "user", "pw")
        >>> results = store.select("block", {"name__icontains": "foo"})

        :param model_name: The name of the model as string.
        :type model_name: str
        :param raw_filters: Filters as defined by the G-Node REST API.
        :type raw_filters: dict

        :returns: A list of (filtered) results.
        :rtype: list
        """
        results = self.rest_store.select(model_name, raw_filters=raw_filters)

        for obj in results:
            self.cache_store.set(obj)

        return results

    def get(self, location, refresh=True, recursive=False):
        """
        Get a single entity from the G-Node REST API. If the entity is already in the cache and refresh
        is True the method will check (using etags) if the entity is still up-to-data and renew it if
        necessary. If recursive is true, all descendants of the entity will be leaded into the cache in
        order to improve performance of subsequent operations.

        :param location: The location or full URL to the entity.
        :type location: str
        :param refresh: If True, update the entity if necessary.
        :type refresh: bool
        :param recursive: Recursively fetch all descendants into the cache.
        :type recursive: bool

        :returns: The entity matching the given location.
        :rtype: Model
        """
        obj = self.cache_store.get(location)

        if obj is None:
            obj = self.rest_store.get(location)
            if obj is not None:
                self.__get_arraydata(obj)
                self.cache_store.set(obj)
        elif refresh:
            obj_refreshed = self.rest_store.get(location, obj.guid)
            if obj_refreshed is not None:
                self.__get_arraydata(obj_refreshed)
                self.cache_store.set(obj_refreshed)
                obj = obj_refreshed

        if recursive:
            self.__get_recursive(location, refresh)

        return obj

    def get_list(self, locations, refresh=True):
        """
        Get a list of objects that are referenced by their locations or complete URLs
        from the G-Node REST API. All results are cached.

        :param locations: List with locations or URLs.
        :type locations: list
        :param refresh: Update cached entities if necessary.
        :type refresh: bool

        :returns: A list of objects matching the list of locations.
        :rtype: list
        """
        results = []
        locations_todo = []

        if refresh:
            locations_todo = locations
        else:
            for loc in locations:
                obj = self.cache_store.get(loc)

                if obj is None:
                    locations_todo.append(loc)
                else:
                    results.append(obj)

        objects = self.rest_store.get_list(locations_todo)

        for obj in objects:
            self.__get_arraydata(obj)
            self.cache_store.set(obj)
            results.append(obj)

        return results

    def get_file(self, location, temporary=False):
        """
        Get raw file data (bytestring) from the store.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: str
        """
        data = self.cache_store.get_file(location, temporary)
        if data is None and not temporary:
            data = self.rest_store.get_file(location)
            self.cache_store.set_file(data, location)
        return data

    def get_array(self, location, temporary=False):
        """
        Read array data from an hdf5 file.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: numpy.ndarray|list
        """
        array_data = self.cache_store.get_array(location, temporary)
        if array_data is None and not temporary:
            data = self.rest_store.get_file(location)
            self.cache_store.set_file(data, location)
            array_data = self.cache_store.get_array(location)
        return array_data

    def set(self, entity, avoid_collisions=False):
        """
        Store an entity that is provided as an instance of RestModel on the server. The returned
        persisted entity is cached locally. If needed the method can check for colliding changes
        of the particular entity on the server, if the entity was previously cached.

        :param entity: The entity that should be persisted.
        :type entity: Model
        :param avoid_collisions: If true and the entity is cached check for colliding changes.
        :type avoid_collisions: bool

        :returns: The persisted entity
        :rtype: Model
        """
        if entity.location is not None:
            old_entity = self.cache_store.get(entity.location)
        else:
            old_entity = None

        # handle temporal datafiles here (array data)
        for field_name in entity:
            field = entity.get_field(field_name)
            field_val = entity[field_name]

            if field.type_info == "datafile" and field_val is not None and field_val["data"] is not None:
                array_location = field_val["data"]
                array = self.cache_store.get_array(array_location, temporary=True)
                if array is not None:
                    # TODO check if file upload is really needed (optimization)
                    new_array_location = self.rest_store.set_array(array)
                    self.cache_store.set_array(array, new_array_location)
                    self.cache_store.delete_file(array_location, temporary=True)
                    entity[field_name]["data"] = new_array_location

        # handle the entity itself
        if old_entity is not None and avoid_collisions:
            entity.guid = old_entity.guid

        obj = self.rest_store.set(entity, avoid_collisions)
        obj = self.cache_store.set(obj)
        return obj

    def set_file(self, data, old_location=None, temporary=False):
        """
        Save raw file data in the store.

        :param data: The raw data of the file.
        :type data: str
        :param old_location: The old location of the file.
        :type old_location: str

        :returns: The url to the stored file.
        :rtype: str
        """
        if old_location is not None:
            self.cache_store.delete_file(old_location)

        if not temporary:
            location = self.rest_store.set_file(data)
            self.cache_store.set_file(data, location)
        else:
            location = self.cache_store.set_file(data, temporary=True)

        return location

    def set_array(self, array_data, old_location=None, temporary=False):
        """
        Save array data in the store.

        :param array_data: The raw data to store.
        :type array_data: numpy.ndarray|list
        :param old_location: The old location of the file.
        :type old_location: str

        :returns: The url to the stored file.
        :rtype: str
        """
        if old_location is not None:
            self.cache_store.delete_file(old_location)

        if not temporary:
            location = self.rest_store.set_array(array_data)
            self.cache_store.set_array(array_data, location)
        else:
            location = self.cache_store.set_array(array_data, temporary=True)

        return location

    def delete(self, entity):
        """
        Delete an entity from the G-Node REST API and from the cache.

        :param entity: The entity to delete.
        :type entity: Model
        """
        self.cache_store.delete(entity)
        self.rest_store.delete(entity)

    def permissions(self, entity, permissions=None):
        """
        Set or get permissions of an object from the G-Node service.

        :param entity: The entity to get or set permissions from/to.
        :type entity: object
        :param permissions: new permissions to apply. It should look like
            {
                "safety_level": 1, # 1-private, 2-friendly, 3-public
                "shared_with": {
                    "bob": 1, # 1-read-only
                    "jeff", 2 # 2-read-write
                }
            }
        :type permissions: dict

        :returns: actual object permissions
        :rtype: dict (see above)
        """
        return self.rest_store.permissions(entity, permissions)

    #
    # Private functions
    #

    # A little helper that makes sure that the array data of an object are on the cache
    def __get_arraydata(self, model_obj):
        for name in model_obj:
            field = model_obj.get_field(name)
            value = model_obj[name]
            if field.type_info == "datafile" and value["data"] is not None and value["units"] is not None:
                # TODO provide a better performing way for checking file existence
                file_location = model_obj[name]["data"]
                data = self.cache_store.get_file(file_location)
                if data is None:
                    data = self.rest_store.get_file(file_location)
                    self.cache_store.set_file(data, file_location)

    def __get_recursive(self, location, refresh):
        locations_done = []
        locations_todo = [urlparse.urlparse(location).path.strip("/")]

        while len(locations_todo) > 0:
            more_locations = []
            objects = self.get_list(locations_todo, refresh)
            locations_done = locations_done + locations_todo

            for obj in objects:
                for field_name in obj.child_fields:
                    field_val = obj[field_name]

                    if field_val is not None and len(field_val) > 0:
                        for val in field_val:
                            val = urlparse.urlparse(val).path.strip("/")
                            if val not in locations_done:
                                more_locations.append(val)

            locations_todo = more_locations
