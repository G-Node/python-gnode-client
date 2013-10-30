# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

class BasicStore(object):
    """
    Abstract definition of a class that can be used to query, read and write data (see: rest_model)
    that is managed by the G-Node REST API.
    """

    def __init__(self, location, user=None, password=None):
        """
        Constructor.

        :param location: The location from where the data should be accessed.
        :type location: str
        :param user: The user name (might be ignored by some kinds of store)
        :type user: str
        :param password: The password (might be ignored by some kinds of store)
        :type password: str
        """
        self.__location = location
        self.__user = user
        self.__password = password

    #
    # Properties
    #

    @property
    def location(self):
        """
        The location from where the data should be accessed. Depending on the implementation
        this can be an URL or a local file or directory.
        """
        return self.__location

    @property
    def user(self):
        """
        The user name (might be ignored by some kinds of store)
        """
        return self.__user

    @property
    def password(self):
        """
        The password (might be ignored by some kinds of store)
        """
        return self.__password

    #
    # Methods
    #

    def connect(self):
        """
        Connect the store to the data source defined by the given location.
        """
        raise NotImplementedError()

    def is_connected(self):
        """
        Test if the store is connected to the data source.

        :returns: True if the store is connected, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError()

    def disconnect(self):
        """
        Disconnect the store from the data source.
        """
        raise NotImplementedError()

    def select(self, model_name, raw_filters=None):
        """
        Select data according to certain criteria. Some implementations of store might not
        implement this method.

        :param model_name: The name of the model/result type e.g. 'analogsignal', 'block' etc.
        :type model_name: str
        :param raw_filters: A raw definition of filters as supported by the G-Node REST API.
        :type raw_filters: dict

        :returns: A list of all results that match the given criteria.
        :rtype: list
        """
        raise NotImplementedError()

    def get(self, location):
        """
        Get an entity from the store.

        :param location: The location of the entity as path or URL.
        :type location: str

        :returns: The entity or None.
        :rtype: Model
        """
        raise NotImplementedError()

    def get_list(self, locations):
        """
        Get an entity from the store.

        :param locations: The locations of all entities as path or URL.
        :type locations: list

        :returns: All entities or an empty list.
        :rtype: list
        """
        raise NotImplementedError()

    def get_file(self, location):
        """
        Get raw file data (bytestring) from the store.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: str
        """
        raise NotImplementedError()

    def get_array(self, location):
        """
        Read array data from an hdf5 file.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: numpy.ndarray|list
        """
        raise NotImplementedError()

    def set(self, entity):
        """
        Save an entity in the store. The type of this entity depends on the implementation of the store
        but in most cases this will be either a structure of dicts and lists or an instance of Model.

        :param entity: The entity to store.
        :type entity: Model

        :returns: The updated entity.
        :rtype: Model
        """
        raise NotImplementedError()

    def set_file(self, data):
        """
        Save raw file data in the store.

        :param data: The raw data of the file.
        :type data: str

        :returns: The url to the uploaded file.
        :rtype: str
        """
        raise NotImplementedError()

    def set_array(self, array_data):
        """
        Save array data in the store.

        :param array_data: The raw data to store.
        :type array_data: numpy.ndarray|list

        :returns: The url to the uploaded file.
        :rtype: str
        """
        raise NotImplementedError()

    def delete(self, entity):
        """
        Remove an entity from the store.

        :param entity: The entity to delete.
        :type entity: Model
        """
        raise NotImplementedError()
