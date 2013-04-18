from utils import *
import os

class Cache( object ):
    """ a class to handle cached objects and data for Session """

    objs_map = {} # map of cached objects, location: reference, like 
    # _cache_map = {
    #   'metadata/section/293847/': '5c142e1ace4bfb766dcec1995428dbd99ea057c7',
    #   'neo/block/198472/': '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f'
    # }

    objs = {} # in-memory cache, contains objects by reference, like
    # _cache_objs = {
    #   '5c142e1ace4bfb766dcec1995428dbd99ea057c7': <Section ...>,
    #   '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f': <Block ...>
    # }

    data_map = {} # map of cached data, contains file paths by id, like
    # _cache_data = {
    #   '538472': '/tmp/538472.h5',
    #   '928464': '/tmp/928464.h5',
    # }

    def __init__(self, cache_dir, cache_file_name, load_cached_data):
        self.cache_dir = cache_dir
        self.cache_file_name = cache_file_name
        if load_cached_data:
            self.load_cached_data()

    def add_object(self, obj):
        """ adds object to cache """
        self.objs_map[ obj._gnode['location'] ] = obj._gnode['guid']
        self.objs[ obj._gnode['guid'] ] = obj

    def clear_cache(self):
        """ removes all objects from the cache """
        self.objs_map = {}
        self.objs = {}
        self.data_map = {}
        self.save_cache()
        # TODO clear files from disk??

    def save_cache(self):
        """ saves cached data map to disk """
        with open(self.cache_dir + self.cache_file_name, 'w') as f:
            f.write( json.dumps(self.data_map) )

    def load_cached_data(self):
        """ loads cached data map from disk and validates cached files """
        try:
            # 1. load cache map
            with open(self.cache_dir + self.cache_file_name, 'r') as f:
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

        except IOError:
            print 'No saved cached data found, cache is empty.'
        except ValueError:
            print 'Cache file cannot be parsed. Skip loading cached data.'


