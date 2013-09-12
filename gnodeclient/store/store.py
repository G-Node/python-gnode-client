

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
