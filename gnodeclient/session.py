from gnodeclient.conf import Configuration
from gnodeclient.store.store import CachingRestStore
from gnodeclient.store.result_driver import NativeDriver

__MAIN_SESSION = None


class Session(object):

    def __init__(self, options, file_name,  persist_options=False):
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
        return self.__options

    #
    # Methods
    #

    def select(self, model_name, raw_filters=None):
        objects = self.__store.select(model_name, raw_filters)
        return [self.__driver.to_result(obj) for obj in objects]

    def get(self, location, refresh=False, recursive=False):
        obj = self.__store.get(location, refresh, recursive)
        res = self.__driver.to_result(obj)
        return res

    def set(self, entity, avoid_collisions=False):
        obj = self.__driver.to_model(entity)
        return obj

    def delete(self, entity, avoid_collisions=False):
        raise NotImplementedError()

    def close(self):
        self.__store.disconnect()


def create(username=None, password=None, location=None, file_name=None, persist_options=False):
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

        __MAIN_SESSION = Session(options, file_name, persist_options)

    return __MAIN_SESSION


def close():
    """
    Close the main session object.
    """
    global __MAIN_SESSION
    if __MAIN_SESSION is not None:
        __MAIN_SESSION.close()
        __MAIN_SESSION = None
