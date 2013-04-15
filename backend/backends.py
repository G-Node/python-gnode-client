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

    def post(self, obj):
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
        json_obj = get_by_location( location )

        if data_load and mode == 'obj':
            


        if mode == obj:



    def post(self, obj):
        """ creates/updates an object, returns updated JSON representation """
        data_refs = self.save_related_data( obj )
        json_obj = Serializer.serialize(obj, self, data_refs)

        cls = get_type_by_obj( obj )
        app = self._meta.app_prefix_dict[cls]

        if hasattr(obj, '_gnode'): # existing object, overwrite in cache
            name = obj._gnode['id']
            status = 200

        else: # new object, create
            name = get_uid()
            status = 201

        location = '%s%s/%s/' % (self._meta.host, app, cls)
        arr = np.array( json.dumps(json_obj) )
        save_to_location(location, name, arr)


    def save_to_location(self, location, name, arr)
        with tb.openFile( self.path, "a" ) as f:
            f.createArray(location, name, arr)

    def get_by_location(self, location):
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


    def detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        attrs_to_sync = []
        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( obj )

        for attr in data_attrs:

            link = obj._gnode['fields'][ attr ]['data']
            location = urlparse.urlparse( link ).path
            init_arr = self.get_by_location( location )

            if not init_arr == None:

                # get actual array
                getter = data_fields[attr][2]
                if getter == 'self':
                    curr_arr = obj # some NEO objects like signal inherit array
                else:
                    curr_arr = getattr(obj, getter)

                if len(curr_arr) < 2:
                    # we treat array with < 2 values as when object was 
                    # fetched without data for performance reasons. in this 
                    # case we ignore this data attribute
                    continue

                # compare cached (original) and current data
                if not np.array_equal(init_arr, curr_arr):
                    attrs_to_sync.append( attr )

            else: # no real reference! treat as array was changed
                attrs_to_sync.append( attr )

        return attrs_to_sync


    def save_related_data(self, obj):
        """ saves array data to disk in HDF5 and uploads new datafiles to the 
        server according to the arrays of the given obj. Saves datafile objects 
        to cache """
        data_refs = {} # returns all updated references to the related data
        model_name = get_type_by_obj( obj )

        data_attrs = self._meta.get_array_attr_names( obj ) # all array-type attrs

        if not hasattr(obj, '_gnode'): # True if object never synced
            # sync all arrays
            attrs_to_sync = data_attrs

        else:
            # sync only changed arrays
            attrs_to_sync = self._detect_changed_data_fields( obj )

        for attr in data_attrs: # attr is like 'times', 'signal' etc.

            if attr in attrs_to_sync:
                # 1. get current array and units
                fname = self._meta.app_definitions[model_name]['data_fields'][attr][2]
                if fname == 'self':
                    arr = obj # some NEO objects like signal inherit array
                else:
                    arr = getattr(obj, fname)

                units = Serializer.parse_units(arr)

                # 2. save it to the cache_dir as HDF5 file
                location = '/datafiles/'
                name = get_uid()
                self.save_to_location( location, name, arr )

            else:
                data_refs[ attr ] = None

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




class Remote( BaseBackend ):
    pass

