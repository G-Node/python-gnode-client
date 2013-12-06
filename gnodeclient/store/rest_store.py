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
import tempfile

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse

from requests_futures.sessions import FuturesSession

import gnodeclient.store.convert as convert
from gnodeclient.model.models import Model
from gnodeclient.store.basic_store import BasicStore
from gnodeclient.util.helper import id_from_location
from gnodeclient.util.hdfio import store_array_data, read_array_data


class RestStore(BasicStore):
    """
    Implementation of Abstract store, that uses the gnode REST API as
    data source.
    """

    URL_LOGIN = 'account/authenticate/'
    URL_LOGOUT = 'account/logout/'

    def __init__(self, location, user, password):
        """
        Constructor.

        :param location: The location from where the data should be accessed.
        :type location: str
        :param user: The user name (might be ignored by some kinds of store)
        :type user: str
        :param password: The password (might be ignored by some kinds of store)
        :type password: str
        """
        super(RestStore, self).__init__(location, user, password)
        self.__session = None

    #
    # Methods
    #

    def connect(self):
        """
        Connect to the G-Node REST API via HTTP. Note: almost all methods throw an HTTPError or
        URLError if the communication fails.
        """
        url = urlparse.urljoin(self.location, RestStore.URL_LOGIN)

        session = FuturesSession(max_workers=20)

        future = session.post(url, {'username': self.user, 'password': self.password})
        response = future.result()
        response.raise_for_status()

        if not session.cookies:
            raise RuntimeError("Unable to authenticate for user '%s' (status: %d)!"
                               % (self.user, response.status_code))

        self.__session = session

    def is_connected(self):
        """
        Check if the BasicStore is connected.

        :returns: bool
        """
        return False if self.__session is None else True

    def disconnect(self):
        """
        Disconnect from the G-Node REST API and discard all session information.
        """
        url = urlparse.urljoin(self.location, RestStore.URL_LOGOUT)

        future = self.__session.get(url)
        response = future.result()
        response.raise_for_status()

        self.__session = None

    def select(self, model_name, raw_filters=None):
        """
        Select data from a certain type e.g. blocks or spiketrains from the G-Node REST API
        and convert the results to a list of model objects.

        :param model_name: The name of the model as string.
        :type model_name: str
        :param raw_filters: Filters as defined by the G-Node REST API.
        :type raw_filters: dict

        :returns: A list of (filtered) results.
        :rtype: list
        """
        results = []

        raw_filters = {} if raw_filters is None else raw_filters

        location = Model.get_location(model_name)
        url = urlparse.urljoin(self.location, location)

        headers = {}
        future = self.__session.get(url, headers=headers, params=raw_filters)
        response = future.result()
        response.raise_for_status()

        raw_results = convert.json_to_collections(response.content, as_list=True)
        for obj in raw_results:
            results.append(convert.collections_to_model(obj))

        return results

    def get(self, location, etag=None):
        """
        Get a single object from the G-Node REST API. If an etag is provided it will be included in
        the request with 'If-none-match'. If the response is 304 the return value of this method will
        be None.

        :param location: The location of the object or the whole URL.
        :type location: str
        :param etag: The etag of the cached object.
        :type etag: str

        :returns: The found object or None if it was not updated.
        :rtype: Model

        :raises: HTTPError if the entity was not found on the server (404).
        """
        if location.startswith("http://"):
            url = location
        else:
            url = urlparse.urljoin(self.location, location)

        headers = {}
        if etag is not None:
            headers['If-none-match'] = etag
        future = self.__session.get(url, headers=headers)
        response = future.result()

        if response.status_code in (304, 404):
            result = None
        else:
            response.raise_for_status()
            result = convert.collections_to_model(convert.json_to_collections(response.content))

        return result

    def get_list(self, locations):
        """
        Get a list of objects that are referenced by their locations or complete URLs
        from the G-Node REST API. In order to get a better performance this method uses
        the features of the requests_futures package.

        :param locations: List with locations or URLs.
        :type locations: list

        :returns: A list of objects matching the list of locations.
        :rtype: list
        """
        futures = []
        results = []

        for location in locations:
            if location.startswith("http://"):
                url = location
            else:
                url = urlparse.urljoin(self.location, location)

            future = self.__session.get(url)
            futures.append(future)

        for future in futures:
            response = future.result()
            response.raise_for_status()

            result = convert.collections_to_model(convert.json_to_collections(response.content))
            results.append(result)

        return results

    def get_file(self, location):
        """
        Get raw file data (bytestring) from the G-Node REST API.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: str
        """
        fid = id_from_location(location)
        url = urlparse.urljoin(self.location, '%s/%s/%s/' % ('datafiles/datafile', fid, 'data'))

        future = self.__session.get(url)
        response = future.result()
        response.raise_for_status()
        return response.content

    def get_array(self, location):
        """
        Get raw file data from the G-Node REST API, store it temporarily as an HDF5 file
        and extract the array data from the file.

        :param location: The locations of all entities as path or URL.
        :type location: str

        :returns: The raw file data.
        :rtype: numpy.ndarray|list
        """
        tmphandler, tmppath = tempfile.mkstemp()
        with open(tmppath, 'w') as f:
            f.write(self.get_file(location))

        array_data = read_array_data(tmppath)
        os.remove(tmppath)
        return array_data

    def set(self, entity, avoid_collisions=False):
        """
        Update or create an entity on the G-Node REST API. If an etag/guid is provided by the entity it
        will be included in the header with 'If-match' if avoid_collisions is True.

        :param entity: The entity to persist.
        :type entity: Model
        :param avoid_collisions: Try to avoid collisions (lost update problem)
        :type avoid_collisions: bool

        :returns: The updated entity.
        :rtype: Model

        :raises: RuntimeError If the changes collide with remote changes of the entity.
        """
        if hasattr(entity, "location") and entity.location is not None:
            url = urlparse.urljoin(self.location, entity.location)
        else:
            url = urlparse.urljoin(self.location, Model.get_location(entity.model))
        data = convert.model_to_json_response(entity)
        headers = {}
        if avoid_collisions and entity.guid is not None:
            headers['If-match'] = entity.guid

        future = self.__session.post(url, data=data, headers=headers)
        response = future.result()

        if response.status_code == 304:
            result = entity
        else:
            response.raise_for_status()
            result = convert.collections_to_model(convert.json_to_collections(response.content))

        return result

    def set_file(self, data):
        """
        Save raw file data on the G-Node REST API.

        :param data: The raw data of the file.
        :type data: str

        :returns: The url to the uploaded file.
        :rtype: str
        """
        files = {'raw_file': data}
        url = urlparse.urljoin(self.location, 'datafiles/datafile/')

        future = self.__session.post(url, files=files)
        response = future.result()
        response.raise_for_status()

        datafile = convert.json_to_collections(response.content)
        return datafile['location']

    def set_array(self, array_data):
        """
        Create a temporary HDF5 file with the array data and upload the file
        data to the G-Node REST API.

        :param array_data: The raw data to store.
        :type array_data: numpy.ndarray|list

        :returns: The url to the uploaded file.
        :rtype: str
        """
        tmphandler, tmppath = tempfile.mkstemp()
        store_array_data(tmppath, array_data)
        with open(tmppath, 'rb') as f:
            location = self.set_file(f.read())
        os.remove(tmppath)
        return location

    def delete(self, entity):
        """
        Delete an entity from the G-Node REST API.

        :param entity: The entity to delete.
        :type entity: Model
        """
        if hasattr(entity, "location") and entity.location is not None:
            url = urlparse.urljoin(self.location, entity.location)
        else:
            raise RuntimeError("The entity has no location and can therefore not be deleted.")

        future = self.__session.delete(url)
        response = future.result()
        response.raise_for_status()

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
        if hasattr(entity, "location") and entity.location is not None:
            base_url = entity.location
            if not base_url.endswith('/'):
                base_url += '/'
            url = urlparse.urljoin(self.location, base_url + 'acl/')
        else:
            raise ValueError("Please submit object "
                             "to the server before changing permissions")
        if permissions:
            data = convert.permissions_to_json(permissions)
            future = self.__session.post(url, data=data)
        else:
            future = self.__session.get(url)

        response = future.result()
        response.raise_for_status()

        return convert.json_to_permissions(response.content)
