import urlparse
import convert
import copy

from requests_futures.sessions import FuturesSession
from gnodeclient.model.rest_model import Models


class GnodeStore(object):
    """
    Abstract definition of a class that can be used to query, read and write data (see: rest_model)
    that is managed by the G-Node REST API.
    """

    def __init__(self, location, user=None, passwd=None):
        """
        Constructor.

        :param location: The location from where the data should be accessed.
        :type location: str
        :param user: The user name (might be ignored by some kinds of store)
        :type user: str
        :param passwd: The password (might be ignored by some kinds of store)
        :type passwd: str
        """
        self.__location = location
        self.__user = user
        self.__passwd = passwd

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
    def passwd(self):
        """
        The password (might be ignored by some kinds of store)
        """
        return self.__passwd

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
        Select data according to certain criteria.

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
        :rtype: object
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

    def set(self, entity):
        """
        Save an entity in the store. The type of this entity depends on the implementation of the store
        but in most cases this will be either a structure of dicts and lists or an instance of Model.

        :param entity: The entity to store.

        :returns: The updated entity.
        """
        raise NotImplementedError()

    def delete(self, entity):
        """
        Remove an entity from the store.

        :param entity: The entity to delete.
        """
        raise NotImplementedError()


class RestStore(GnodeStore):
    """
    Implementation of Abstract store, that uses the gnode REST API as
    data source.
    """

    URL_LOGIN = 'account/authenticate/'
    URL_LOGOUT = 'account/logout/'

    def __init__(self, location, user, passwd, converter=convert.collections_to_model):
        super(RestStore, self).__init__(location, user, passwd)
        self.__session = None

        if converter is None:
            self.__converter = lambda x: x
        else:
            self.__converter = converter

    #
    # Methods
    #

    def connect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGIN)

        session = FuturesSession(max_workers=20)

        future = session.post(url, {'username': self.user, 'password': self.passwd})
        response = future.result()
        response.raise_for_status()

        if not session.cookies:
            raise RuntimeError("Unable to authenticate for user '%s' (status: %d)!"
                               % (self.user, response.status_code))

        self.__session = session

    def is_connected(self):
        return False if self.__session is None else True

    def disconnect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGOUT)

        future = self.__session.get(url)
        response = future.result()
        response.raise_for_status()

        self.__session = None

    def select(self, model_name, raw_filters=None):
        results = []

        raw_filters = {} if raw_filters is None else raw_filters

        location = Models.location(model_name)
        url = urlparse.urljoin(self.location, location)

        headers = {}
        future = self.__session.get(url, headers=headers, params=raw_filters)
        response = future.result()
        response.raise_for_status()

        raw_results = convert.json_to_collections(response.content, as_list=True)
        for obj in raw_results:
            results.append(self.__converter(obj))

        return results

    def get(self, location, etag=None):
        if location.startswith("http://"):
            url = location
        else:
            url = urlparse.urljoin(self.location, location)

        headers = {}
        if etag is not None:
            headers['If-none-match'] = etag
        future = self.__session.get(url, headers=headers)
        response = future.result()
        response.raise_for_status()

        if response.status_code == 304:
            result = None
        else:
            result = self.__converter(convert.json_to_collections(response.content))

        return result

    def get_list(self, locations):
        futures = []
        results = []

        for location in locations:
            if location.startswith("http://"):
                url = location
            else:
                url = urlparse.urljoin(self.location, location)

            headers = {}

            future = self.__session.get(url, headers=headers)
            futures.append(future)

        for future in futures:
            response = future.result()
            response.raise_for_status()

            result = self.__converter(convert.json_to_collections(response.content))
            results.append(result)

        return results

    def set(self, entity):
        # TODO implement set()
        raise NotImplementedError()

    def delete(self, entity):
        # TODO implement delete()
        raise NotImplementedError()


#TODO now the cache is just in memory, but it should work on disk
class CacheStore(GnodeStore):
    """
    A cache store.
    """

    def __init__(self, location=None, user=None, passwd=None, converter=convert.collections_to_model):
        super(CacheStore, self).__init__(location, user, passwd)

        self.__cache = None

        if converter is None:
            self.__converter = lambda x: x
        else:
            self.__converter = converter

    #
    # Methods
    #

    def connect(self):
        self.__cache = {}

    def is_connected(self):
        return self.__cache is not None

    def disconnect(self):
        del self.__cache
        self.__cache = None

    def get(self, location):
        location = urlparse.urlparse(location).path.strip("/")
        if location in self.__cache:
            obj = copy.deepcopy(self.__cache[location])
            return self.__converter(obj)
        else:
            return None

    def set(self, entity):
        if entity is not None:
            location = urlparse.urlparse(entity['location']).path.strip("/")
            self.__cache[location] = copy.deepcopy(entity)

    def delete(self, entity):
        location = urlparse.urlparse(entity['location']).path.strip("/")
        if location in self.__cache:
            del self.__cache[location]


class CachingRestStore(GnodeStore):

    def __init__(self, location, user, passwd, cache_location=None, converter=convert.collections_to_model):
        super(CachingRestStore, self).__init__(location, user, passwd)

        self.__cache_location = cache_location

        if converter is None:
            self.__converter = lambda x: x
        else:
            self.__converter = converter

        self.__rest_store = RestStore(location, user, passwd, converter=None)
        self.__cache_store = CacheStore(cache_location, converter=converter)

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
        self.rest_store.connect()
        self.cache_store.connect()

    def is_connected(self):
        return self.rest_store.is_connected() and self.cache_store.is_connected()

    def disconnect(self):
        self.rest_store.disconnect()
        self.cache_store.disconnect()

    def select(self, model_name, raw_filters=None):
        results = []
        objects = self.rest_store.select(model_name, raw_filters=raw_filters)

        for obj in objects:
            self.cache_store.set(obj)
            results.append(self.__converter(obj))

        return results

    def get(self, location, refresh=True, recursive=False):
        obj = self.cache_store.get(location)

        if obj is None:
            obj = self.rest_store.get(location)
            self.cache_store.set(obj)
            obj = self.__converter(obj)
        elif refresh:
            obj_refreshed = self.rest_store.get(location, obj.guid)
            if obj_refreshed is not None:
                self.cache_store.set(obj_refreshed)
                obj = self.__converter(obj_refreshed)

        if recursive:
            self.__get_recursive(location, refresh)

        return obj

    def get_list(self, locations, refresh=True):
        results = []
        locations_todo = []

        if refresh:
            locations_todo = locations
        else:
            for location in locations:
                obj = self.cache_store.get(location)

                if obj is None:
                    locations_todo.append(location)
                else:
                    results.append(self.__converter(obj))

        objects = self.__rest_store.get_list(locations_todo)

        for obj in objects:
            self.cache_store.set(obj)
            results.append(self.__converter(obj))

        return results

    def set(self, entity):
        # TODO implement ()
        raise NotImplementedError()

    def delete(self, entity):
        # TODO implement delte()
        raise NotImplementedError()

    #
    # Private functions
    #

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
