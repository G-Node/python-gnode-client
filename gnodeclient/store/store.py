import urlparse
import convert
import copy

from requests_futures.sessions import FuturesSession
from gnodeclient.model.rest_model import Models, RestResult


class GnodeStore(object):
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
        :rtype: RestResult
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
        :type entity: RestResult

        :returns: The updated entity.
        :rtype: RestResult
        """
        raise NotImplementedError()

    def delete(self, entity):
        """
        Remove an entity from the store.

        :param entity: The entity to delete.
        :type entity: RestResult
        """
        raise NotImplementedError()


class RestStore(GnodeStore):
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
        Check if the GnodeStore is connected.

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

        location = Models.location(model_name)
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
        :rtype: RestResult

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
        response.raise_for_status()

        if response.status_code == 304:
            result = None
        else:
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

    def set(self, entity, avoid_collisions=False):
        """
        Update or create an entity on the G-Node REST API. If an etag/guid is provided by the entity it
        will be included in the header with 'If-match' if avoid_collisions is True.

        :param entity: The entity to persist.
        :type entity: RestResult
        :param avoid_collisions: Try to avoid collisions (lost update problem)
        :type avoid_collisions: bool

        :returns: The updated entity.
        :rtype: RestResult

        :raises: RuntimeError If the changes collide with remote changes of the entity.
        """
        if hasattr(entity, "location") and entity.location is not None:
            url = urlparse.urljoin(self.location, entity.location)
        else:
            url = urlparse.urljoin(self.location, Models.location(entity.model))
        data = convert.model_to_json_response(entity)
        headers = {}
        if avoid_collisions and entity.guid is not None:
            headers['If-match'] = entity.guid

        future = self.__session.post(url, data=data, headers=headers)
        response = future.result()
        response.raise_for_status()

        result = convert.collections_to_model(convert.json_to_collections(response.content))
        return result

    def delete(self, entity):
        """
        Delete an entity from the G-Node REST API.

        :param entity: The entity to delete.
        :type entity: RestResult
        """
        if hasattr(entity, "location") and entity.location is not None:
            url = urlparse.urljoin(self.location, entity.location)
        else:
            raise RuntimeError("The entity has no location and can therefore not be deleted.")

        future = self.__session.delete(url)
        response = future.result()
        response.raise_for_status()


class CacheStore(GnodeStore):
    """
    A simple cache store.
    """
    #TODO now the cache is just in memory, replace this with an implementation that works on disk

    def __init__(self, location=None):
        super(CacheStore, self).__init__(location)
        self.__cache = None

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
            return convert.collections_to_model(obj)
        else:
            return None

    def set(self, entity):
        if entity is not None:
            location = urlparse.urlparse(entity.location).path.strip("/")
            entity_data = convert.model_to_collections(entity)
            self.__cache[location] = copy.deepcopy(entity_data)
        return entity

    def delete(self, entity):
        location = urlparse.urlparse(entity['location']).path.strip("/")
        if location in self.__cache:
            del self.__cache[location]


class CachingRestStore(GnodeStore):
    """
    A store implementation, that uses an instance of GnodeStore and CacheStore to implement
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
        :rtype: RestResult
        """
        obj = self.cache_store.get(location)

        if obj is None:
            obj = self.rest_store.get(location)
            self.cache_store.set(obj)
        elif refresh:
            obj_refreshed = self.rest_store.get(location, obj.guid)
            if obj_refreshed is not None:
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
            for location in locations:
                obj = self.cache_store.get(location)

                if obj is None:
                    locations_todo.append(location)
                else:
                    results.append(obj)

        objects = self.__rest_store.get_list(locations_todo)

        for obj in objects:
            self.cache_store.set(obj)
            results.append(obj)

        return results

    def set(self, entity, avoid_collisions=False):
        """
        Store an entity that is provided as an instance of RestModel on the server. The returned
        persisted entity is cached locally. If needed the method can check for colliding changes
        of the particular entity on the server, if the entity was previously cached.

        :param entity: The entity that should be persisted.
        :type entity: RestResult
        :param avoid_collisions: If true and the entity is cached check for colliding changes.
        :type avoid_collisions: bool

        :returns: The persisted entity
        :rtype: RestResult
        """
        if entity.location is not None and avoid_collisions:
            cached = self.__cache_store.get(entity.location)
            if cached is not None:
                entity.guid = cached.guid

        obj = self.__rest_store.set(entity, avoid_collisions)
        obj = self.__cache_store.set(obj)
        return obj

    def delete(self, entity):
        """
        Delete an entity from the G-Node REST API and from the cache.

        :param entity: The entity to delete.
        :type entity: RestResult
        """
        self.cache_store.delete(entity)
        self.rest_store.delete(entity)

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
