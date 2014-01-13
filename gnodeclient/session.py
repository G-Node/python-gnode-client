# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
The session module defines the main programming interface of the G-Node Client. It
provides the Session class which defines all methods, that are necessary to access the
G-Node REST API. Further the module defines the functions crate() and close(): both
functions operate on a global, application wide session object.
"""

from __future__ import print_function, absolute_import, division

from gnodeclient.conf import Configuration
from gnodeclient.store.caching_rest_store import CachingRestStore
from gnodeclient.result.result_driver import NativeDriver

__all__ = ("Session", "create", "close")

# A global session object.
_MAIN_SESSION = None


class Session(object):
    """
    The session class defines all basic methods, that are necessary to access the the
    G-Node REST API.
    """

    def __init__(self, options, file_name, persist_options=False):
        """
        Constructor.

        :param options: A dict with configuration options such as 'username', 'password' or 'location'.
        :type options: dict
        :param file_name: A path to a file that contains further configuration options.
        :type file_name: str
        :param persist_options: If set to True, all options will be saved in the configuration
                                file (except for the password).

        """
        self.__options = Configuration(options, file_name, persist_options)
        self.__store = CachingRestStore(location=self.__options["location"], user=self.__options["username"],
                                        password=self.__options["password"])
        self.__store.connect()
        self.__driver = NativeDriver(self.__store)

    #
    # Properties
    #

    @property
    def options(self):
        """
        Read only property for accessing all used options.

        :returns: All currently used options.
        :rtype: Configuration
        """
        return self.__options

    #
    # Methods
    #

    def select(self, model_name, raw_filters=None):
        """
        Obtain a list of objects from a certain kind from the G-Node service. In addition
        a set of filters can be applied in order to reduce the returned results.

        :param model_name: The name of the model e.g. 'block' or 'spike'.
        :type model_name: str
        :param raw_filters: A set of filters as used by the G-Node REST API e.g. {'name_icontains': 'foo'}
        :type raw_filters: dict

        :returns: A list of objects.
        :rtype: list
        """
        objects = self.__store.select(model_name, raw_filters)
        return [self.__driver.to_result(obj) for obj in objects]

    def get(self, location, refresh=False, recursive=False):
        """
        Get a specific object from the G-Node service. The object to obtain is specified by its location.

        :param location: The location of the object.
        :type location: str
        :param refresh: If True and if the object was previously cached, check if it has changed.
        :type refresh: bool
        :param recursive: If True, load all child objects recursively to the cache.
        :type recursive: bool

        :returns: The requested object (Neo or odML).
        """
        obj = self.__store.get(location, refresh, recursive)
        if obj is not None:
            res = self.__driver.to_result(obj)
        else:
            res = None
        return res

    def set(self, entity, avoid_collisions=False):
        """
        Save a modified or created object on the G-Node service.

        :param entity: The object to store (Neo or odML).
        :type entity: object
        :param avoid_collisions: If true, check if the modified object collide with changes on the server.
        :type avoid_collisions: bool

        :returns: The saved entity.
        :rtype: object
        """
        obj = self.__driver.to_model(entity)
        mod = self.__store.set(obj, avoid_collisions)
        res = self.__driver.to_result(mod)
        return res

    def delete(self, entity):
        """
        Delete an object from the G-Node service.

        :param entity: The entity to delete.
        :type entity: object
        """
        obj = self.__driver.to_model(entity)
        self.__store.delete(obj)

    def permissions(self, entity, permissions=None):
        """
        Set or get permissions of an object from the G-Node service.

        The permissions object, that is passed as a second parameter
        contains the following information:

        .. code-block:: python

            {
                "safety_level": 1, # 1-private, 2-friendly, 3-public
                "shared_with": {
                    "bob": 1, # 1-read-only
                    "jeff", 2 # 2-read-write
                }
            }

        :param entity: The entity to get or set permissions from/to.
        :type entity: object
        :param permissions: new permissions to apply.

        :type permissions: dict

        :returns: actual object permissions
        :rtype: dict (see above)
        """
        return self.__store.permissions(entity, permissions)

    def close(self):
        """
        Close all connections and opened files used by the session.
        """
        self.__store.disconnect()

    def is_open(self):
        return self.__store.is_connected()

    def clear_cache(self):
        self.__store.cache_store.clear_cache()


def create(username=None, password=None, location=None, file_name=None, persist_options=False):
    """
    Creates and returns a main session object. Multiple calls will return always
    the same object unless close() was not called.
    """
    global _MAIN_SESSION
    if _MAIN_SESSION is None:
        options = {}
        if username is not None:
            options["username"] = username
        if password is not None:
            options["password"] = password
        if location is not None:
            options["location"] = location

        _MAIN_SESSION = Session(options, file_name, persist_options)

    return _MAIN_SESSION


def close():
    """
    Close the main session object.
    """
    global _MAIN_SESSION
    if _MAIN_SESSION is not None:
        _MAIN_SESSION.close()
        _MAIN_SESSION = None
