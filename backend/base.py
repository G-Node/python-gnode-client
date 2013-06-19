
class BaseBackend( object ):
    """ abstract class defining public interface for any client backend. """

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

    def get(self, location, params={}, etag=None):
        """ returns a JSON representation of a single object """
        raise NotImplementedError

    def get_data(self, location, cache_dir=None):
        """ fetches data by a given location. stores data at a given cache_dir,
        if needed. returns a {"id": <id of the data object>, "path": <path to 
        the fetched object>, "data": <data itself>} """
        raise NotImplementedError

    def get_list(self, model_name, params={}):
        """ returns a list of object JSON representations """
        raise NotImplementedError

    def save(self, json_obj):
        """ creates/updates an object, returns updated JSON representation """
        raise NotImplementedError

    def save_data(self, datapath):
        """ saves a given array at datapath. returns saved object as JSON """
        raise NotImplementedError

    def save_list(self, model_name, json_obj, params={}):
        """ applies changes to all available objects of a given model, filtered
        using the criterias defined in params. Changes should be represented in
        a json_obj. """
        raise NotImplementedError

    def delete(self, location):
        """ deletes an object at a certain location """
        raise NotImplementedError



