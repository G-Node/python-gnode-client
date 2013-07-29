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

    def add_object(self, obj):
        """ adds object to cache """
        location = self._meta.clean_location( obj._gnode['location'] )
        guid = obj._gnode['fields']['guid']
        self.objs_map[ location ] = guid
        self.objs[ guid ] = obj

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


