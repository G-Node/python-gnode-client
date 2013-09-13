import requests
import urlparse
import convert


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

    def get(self, location):
        """
        Get an entity from the store.

        :param location: The location of the entity as path or URL.
        :type location: str

        :returns: The entity or None.
        """
        raise NotImplementedError()

    def set(self, entity):
        """
        Save an entity in the store. The type of this entity depends on the implementation of the store
        but in most cases this will be either a structure of dicts and lists or an instance of Model.

        :param entity: The entity to store.
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
        self.__cookies = None

        if converter is None:
            self.__converter = lambda x: x
        else:
            self.__converter = converter

    #
    # Methods
    #

    def connect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGIN)

        response = requests.post(url, {'username': self.user, 'password': self.passwd})
        response.raise_for_status()

        if not response.cookies:
            raise RuntimeError("Unable to authenticate for user '%s' (status: %d)!"
                               % (self.user, response.status_code))

        self.__cookies = response.cookies

    def is_connected(self):
        return False if self.__cookies is None else True

    def disconnect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGOUT)
        requests.get(url, cookies=self.__cookies)
        self.__cookies = None

    def get(self, location, etag=None):
        if location.startswith("http://"):
            url = location
        else:
            url = urlparse.urljoin(self.location, location)

        headers = {}
        if etag is not None:
            headers['If-none-match'] = etag

        response = requests.get(url, headers=headers, cookies=self.__cookies)
        response.raise_for_status()

        if response.status_code == 304:
            result = None
        else:
            result = self.__converter(convert.json_to_collections(response.content))

        return result

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
            return self.__converter(self.__cache[location])
        else:
            return None

    def set(self, entity):
        if entity is not None:
            location = urlparse.urlparse(entity['location']).path.strip("/")
            self.__cache[location] = entity

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

    def get(self, location, refresh=True):

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

        return obj

    def set(self, entity):
        # TODO implement ()
        raise NotImplementedError()

    def delete(self, entity):
        # TODO implement delte()
        raise NotImplementedError()
