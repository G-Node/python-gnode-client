import requests
import urlparse
import convert

from requests.exceptions import ConnectionError


class AbstractStore(object):

    def __init__(self, location, user=None, passwd=None):
        self.__location = location
        self.__user = user
        self.__passwd = passwd

    #
    # Properties
    #

    @property
    def location(self):
        return self.__location

    @property
    def user(self):
        return self.__user

    @property
    def passwd(self):
        return self.__passwd

    #
    # Methods
    #

    def connect(self):
        raise NotImplementedError()

    def is_connected(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def get(self, location=None):
        raise NotImplementedError()

    def set(self, entity):
        raise NotImplementedError()

    def delete(self, entity):
        raise NotImplementedError()


class RestStore(AbstractStore):

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
    # Properties
    #

    @property
    def converter(self):
        return self.__converter

    #
    # Methods
    #

    def connect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGIN)

        response = requests.post(url, {'username': self.user, 'password': self.passwd})
        response.raise_for_status()

        if not response.cookies:
            raise ConnectionError("Unable to authenticate for user '%s' (status: %d)!"
                                  % (self.user, response.status_code))

        self.__cookies = response.cookies

    def is_connected(self):
        return False if self.__cookies is None else True

    def disconnect(self):
        url = urlparse.urljoin(self.location, RestStore.URL_LOGOUT)
        requests.get(url, cookies=self.__cookies)
        self.__cookies = None

    def get(self, location=None, etag=None):
        """
        Exceptions: HTTPError, ConnectionError
        """
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

    def set(self, model):
        # TODO implement set()
        raise NotImplementedError()

    def delete(self, model):
        # TODO implement delete()
        raise NotImplementedError()
