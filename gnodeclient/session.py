from gnodeclient.conf import Configuration
from gnodeclient.store import CachingRestStore

__MAIN_SESSION = None


class Session(object):

    def __init__(self, options, file_name):
        self.__options = Configuration(options, file_name)
        self.__store = CachingRestStore(location=self.__options["location"], user=self.__options["username"],
                                        passwd=self.__options["password"])
        self.__store.connect()

    #
    # Properties
    #

    @property
    def options(self):
        return self.__options

    #
    # Methods
    #

    def get(self, location, refresh=False):
        return self.__store.get(location, refresh)

    def close(self):
        self.__store.disconnect()


def create(username=None, password=None, location=None, file_name=None):
    """
    Creates and returns a main session object. Multiple calls will return always
    the same object unless close() was not called.
    """
    global __MAIN_SESSION
    if __MAIN_SESSION is None:
        options = {}
        if username is not None:
            options["username"] = username
        if password is not None:
            options["password"] = password
        if location is not None:
            options["location"] = location

        __MAIN_SESSION = Session(options, file_name)

    return __MAIN_SESSION


def close():
    """
    Close the main session object.
    """
    global __MAIN_SESSION
    if __MAIN_SESSION is not None:
        __MAIN_SESSION.close()
        __MAIN_SESSION = None
