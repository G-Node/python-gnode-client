import tables as tb
import os

from utils import *
from models import get_type_by_obj
from tables.exceptions import NoSuchNodeError

class BaseBackend( object ):
    """ abstract class for a client backend """

    def get(self, location, params={}, data_load=False):
        """ returns a single object or it's JSON representation """
        raise NotImplementedError

    def get_list(self, cls, params={}, data_load=False):
        """ returns a list of objects or their JSON representations """
        raise NotImplementedError

    def save(self, obj):
        """ creates/updates an object, returns updated JSON representation """
        raise NotImplementedError


class Local( BaseBackend ):

    def __init__(self, cache_dir, cache_file_name, meta):
        self.cache_dir = cache_dir
        self.cache_file_name = cache_file_name
        self.path = cache_dir + cache_file_name
        self._meta = meta # FIXME bad to reference the same object with session
        self.init_hdf5_storage()

    def get(self, location, params={}, data_load=False, mode='obj'):
        """ returns a single object or it's JSON representation """
        json_obj = _get_by_location( location )

        if data_load and mode == 'obj':
            


        if mode == obj:



    def save(self, obj):
        """ creates/updates an object, returns updated JSON representation """
        data_refs = self.save_data( obj )
        json_obj = Serializer.serialize(obj, self, data_refs)

        cls = get_type_by_obj( obj )
        app = self._meta.app_prefix_dict[cls]
        location = json_obj['location']

        if hasattr(obj, '_gnode'): # existing object, should be in cache
            json_cached = self._get_by_location( location )

            if not json_cached == None:
                if json_cached == json_obj:
                    return 304 # object not modified

            self._save_to_location(location, name, json_obj)
            return 200 # successfuly saved

        else: # new object, create
            self._save_to_location(location, name, json_obj)
            return 201 # successfully created

    def save_data(self, obj):
        """ saves array data to disk in HDF5 and uploads new datafiles to the 
        server according to the arrays of the given obj. Saves datafile objects 
        to cache.

        returns:
        data_refs - all updated references to the related data, like
                    {'signal': {
                            'data': '/datafiles/28374',
                            'units': 'mV'
                        },
                    ...
                    }
        """
        data_refs = {} 

        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( obj ) # all array-type attrs

        for attr in data_attrs: # attr is like 'times', 'signal' etc.

            # 1. get current array and units
            getter = data_fields[attr][2]
            if getter == 'self':
                curr_arr = obj # some NEO objects like signal inherit array
            else:
                curr_arr = getattr(obj, getter)

            units = Serializer.parse_units(arr)

            if len(curr_arr) < 2:
                # we treat array with < 2 values as when object was 
                # fetched without data for performance reasons. in this 
                # case we ignore this data attribute
                continue

            # 2. search for cached array
            link = obj._gnode['fields'][ attr ]['data']
            location = urlparse.urlparse( link ).path
            init_arr = self._get_by_location( location )

            if not init_arr == None: # cached array exists
                # compare cached (original) and current data
                if np.array_equal(init_arr, curr_arr):
                    continue # no changes needed

            # 3. save as new array
            location = '/datafiles/'
            name = get_uid()
            self._save_to_location( location, name, curr_arr )

            data_refs[ attr ] = {'data': location, 'units': units}

        return data_refs


    def init_hdf5_storage(self):
        """ checks a cache file exists on disk """
        try:
            if os.path.exists( self.path ) and tb.isHDF5( self.path ):
                print_status( 'Cache file with %s data found.' %  \
                    sizeof_fmt( os.path.getsize( self.path )))

        except IOError:
            print 'No saved cached data found, cache is empty.'
        except ValueError:
            print 'Cache file cannot be parsed. Skip loading cached data.'

    #---------------------------------------------------------------------------
    # cache file operations
    #---------------------------------------------------------------------------

    def _save_to_location(self, location, name, obj)
        """ saves (ovewrites if exists) a given JSON or array obj to the cache 
        file at a given location with a given name """
        try: # JSON object
            to_save = json.dumps(obj)
            to_save = np.array( to_save )

        except TypeError:
            pass # array given

        with tb.openFile( self.path, "a" ) as f:
            # FIXME overwrite if exists
            try:
                f.removeNode( location, name )
            except NoSuchNodeError:
                pass

            f.createArray(location, name, arr)


    def _get_by_location(self, location):
        """ """
        try:
            with tb.openFile( self.path, "r" ) as f:
                node = f.getNode(location)

        except NoSuchNodeError:
            return None

        try: # JSON data
            obj = json.loads( str(node.read()) )

        except ValueError: # array data
            obj = np.array( node.read() )

        return obj



class Remote( BaseBackend ):
    pass

