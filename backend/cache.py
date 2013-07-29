from utils import *

import os
import tables as tb
import numpy as np

class Cache( object ):
    """ a class to handle cached objects and data for Session """

    objs = {} # in-memory cache, contains objects by reference, like
    # _cache_objs = {
    #   '5c142e1ace4bfb766dcec1995428dbd99ea057c7': <Section ...>,
    #   '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f': <Block ...>
    # }

    objs_map = {} # map of cached objects, location: reference, like 
    # _cache_map = {
    #   'metadata/section/293847/': '5c142e1ace4bfb766dcec1995428dbd99ea057c7',
    #   'neo/block/198472/': '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f'
    # }

    data_map = {} # map of cached data, contains file paths by id, like
    # _cache_data = {
    #   '538472': '/.cache/538472.h5',
    #   '928464': '/.cache/928464.h5',
    # }

    def __init__(self, meta):
        self._meta = meta
        if meta.load_cached_data:
            self.load_cached_data()

    def update_object(self, obj):
        """ adds/updates object in the cache (non-cascade) """
        model_name = get_type_by_obj(obj)
        app_name = self._meta.app_prefix_dict[ model_name ]
        json_obj = {}
        data_refs = {}

        # 1. detect / generate IDs
        if hasattr(obj, '_gnode'): # synced object
            guid = obj._gnode['fields']['guid']
            location = self._meta.clean_location( obj._gnode['location'] )

        else:
            lid = generate_temp_id()
            guid = generate_temp_guid()
            location = "/%s/%s/%s/" % (app_name, model_name, lid)

        # 2. save data if new or was changed
        attrs_to_save = self.__detect_changed_data_fields(obj)
        for attr in attrs_to_save:
            fname = self._meta.app_definitions[model_name]['data_fields'][attr][2]
            if fname == 'self':
                arr = obj # some NEO objects like signal inherit array
            else:
                arr = getattr(obj, fname)

            if not type(arr) == type(None): # because of NEO __eq__
                units = Serializer.parse_units(arr)
                datapath = self._cache.save_data(arr)
                data_refs[ attr ] = {'data': datalink, 'units': units}

            else:
                data_refs[ attr ] = None

        # 3. update cached values
        self.objs_map[ location ] = guid
        self.objs[ guid ] = obj

        json_obj['guid'] = guid
        json_obj['location'] = location
        json_obj['new_data_references'] = data_refs
        return json_obj


    def clear_cache(self):
        """ removes all objects from the cache """
        self.objs_map = {}
        self.objs = {}
        self.data_map = {}
        self.save_cache()
        # TODO clear files from disk??

    def save_cache(self):
        """ saves cached data map to disk """
        # 1. loop over all objs, save data to disk if not yet done, update 
        # data_map with new file references

        # 2. save file references in data_map.json
        with open(self._meta.cache_path, 'w') as f:
            f.write( json.dumps(self.data_map) )

        # 3. save object references in data_map.json

        # 4. loop over objs and serialize all to JSON, save


    def load_cached_data(self):
        """ loads cached data map from disk and validates cached files """
        if not os.path.exists( self._meta.cache_path ):
            print 'No saved cached data found, cache is empty.'

        else:
            try:
                # 1. load cache map
                with open(self._meta.cache_path, 'r') as f:
                    data_map = json.load(f)
                print_status( 'Cache file found. Loading...' )
                
                # 2. validate map
                not_found = []
                for lid, filepath in data_map.items():
                    if os.path.exists( filepath ):
                        self.data_map[ lid ] = filepath
                    else:
                        not_found.append( filepath )
                if not_found:
                    to_render = str( not_found )[:100]
                    print 'Some cached files cannot be found, remove them from cache: %s' % to_render

                print 'Cache loaded (%d).' % len( self.data_map.keys() )

            except ValueError:
                print 'Cache file cannot be parsed. Skip loading cached data.'


    def get_data(self, location):
        """ returns a data-array from cached file on disk. None if not exist """
        fid = str( get_id_from_permalink( location ) )

        if not self.data_map.has_key( fid ):
            return None

        with tb.openFile( self.data_map[ fid ], 'r') as f:
            carray = f.listNodes( "/" )[0]
            data = np.array( carray[:] )

        return {"id": fid, "path": self.data_map[ fid ], "data": data}


    def save_data(self, arr):
        """ saves a given array to the cache_dir as HDF5 file """
        cache_dir = self._meta.cache_dir
        temp_name = hashlib.sha1( arr ).hexdigest()
        datapath = os.path.join(cache_dir, temp_name + '.h5')
        with tb.openFile( datapath, "w" ) as f:
            f.createArray('/', 'gnode_array', arr)

        return datapath


    def __detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        attrs_to_sync = []
        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( model_name )

        if not hasattr(obj, '_gnode'):
            return data_attrs # object is new, all data attrs must be saved

        for attr in data_attrs:

            data_value = obj._gnode['fields'][ attr ]['data']

            if data_value:
                data_info = self.get_data( data_value )

                if not data_info == None:
                    # get actual array
                    getter = data_fields[attr][2]
                    if getter == 'self':
                        # some NEO objects like signal inherit array
                        curr_arr = obj
                    else:
                        curr_arr = getattr(obj, getter)

                    if len(curr_arr) < 2:
                        # we treat array with < 2 values as when object was 
                        # fetched without data for performance reasons. in this 
                        # case we ignore this data attribute
                        continue

                    # compare cached (original) and current data
                    if not np.array_equal(data_info['data'], curr_arr):
                        attrs_to_sync.append( attr )

                else: # no data!
                    attrs_to_sync.append( attr )

            else: # no real reference! treat as array was changed
                attrs_to_sync.append( attr )

        return attrs_to_sync

