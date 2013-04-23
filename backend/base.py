
class BaseBackend( object ):
    """ public interface for a client backend. Backend talks JSON + HDF5. """

    #---------------------------------------------------------------------------
    # open/close backend (authenticate etc.)
    #---------------------------------------------------------------------------

    def open(self):
        """ opens the backend for writing """
        raise NotImplementedError

    def close(self):
        """ closes the backend """
        raise NotImplementedError

    @property
    def is_active(self):
        """ is opened or not """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # backend supported operations
    #---------------------------------------------------------------------------

    def get(self, location, params={}):
        """ returns a JSON representation of a single object """
        raise NotImplementedError

    def get_list(self, model_name, params={}):
        """ returns a list of object JSON representations """
        raise NotImplementedError

    def get_data(self, location):
        """ returns a filepath + path in the file to the data array """
        raise NotImplementedError

    def save(self, json_obj):
        """ creates/updates an object, returns updated JSON representation """
        raise NotImplementedError

    def save_data(self, data, location=None):
        """ saves a given array at location. returns an id of the saved 
        object """
        raise NotImplementedError
