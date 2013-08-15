"""
This module is an attempt to implement a simple local HDF5 backend.

For the moment this module is not used, a Cache is used instead.
See the cache.py module for details.

"""


import tables as tb
import numpy as np

import os

from tables.exceptions import NoSuchNodeError
from base import BaseBackend
from utils import *

class Local( BaseBackend ):

    def __init__(self, meta):
        self._meta = meta
        self.init_hdf5_storage()

    def init_hdf5_storage(self):
        """ checks a cache file exists on disk """
        def get_or_create( where, name ):
            try:
                f.getNode( where + name )

            except NoSuchNodeError:
                f.createGroup( where, name )

        try:
            if not os.path.exists( self._meta.cache_dir ):
                os.makedirs( self._meta.cache_dir )

            with tb.openFile( self._meta.cache_path, 'a' ) as f:
                get_or_create( '/', 'datafiles' )

                for model_name, app in self._meta.app_prefix_dict.items():

                    # check the app group exists
                    get_or_create( '/', app )

                    # check the model group exists
                    get_or_create( '/' + app + '/', model_name )

            print_status( 'Cache file with %s data found.\n' %  \
                sizeof_fmt( os.path.getsize( self._meta.cache_path )))

        except IOError, e:
            print 'No saved cached data found, cache is empty.'
        except ValueError:
            print 'Cache file cannot be parsed. Skip loading cached data.'

    #---------------------------------------------------------------------------
    # open/close backend (authenticate etc.)
    #---------------------------------------------------------------------------

    def open(self):
        """ opens the backend for writing """
        self.f = tb.openFile( self._meta.cache_path, "a" )

    def close(self):
        """ closes the backend """
        self.f.close()
        del(self.f)

    @property
    def is_active(self):
        """ is opened or not """
        return hasattr(self, 'f')

    #---------------------------------------------------------------------------
    # backend supported operations
    #---------------------------------------------------------------------------

    def get(self, location, params={}):
        """ returns a JSON or array object from the object at a given location
        in the cache file. None if not exist """
        if is_permalink( location ):
            location = extract_location( location )

        try:
            node = self.f.getNode(location)
        except NoSuchNodeError:
            return None

        obj = json.loads( str(node.read()) )
        return obj


    def get_data(self, location):
        """ returns a filepath + path in the file to the data array """
        fid = get_id_from_permalink( location )

        try:
            node = self.f.getNode('/datafiles/' + str(fid))
        except NoSuchNodeError:
            return None

        obj = np.array( node.read() )
        return obj

    def get_list(self, model_name, params={}):
        """ get a list of objects of a certain type from the cache file """
        app = self._meta.app_prefix_dict[ model_name ]

        path = "/%s/%s" % (app, model_name)

        try:
            nodes = self.f.listNodes( path )
        except NoSuchNodeError:
            return None

        json_list = []
        for node in nodes:
            json_list.append( json.loads( str(node.read()) ) )

        json_list = self.apply_filter( json_list, params )
        return json_list

    def save(self, json_obj):
        """ bla foo """
        app, model_name, lid = self._meta.parse_location( json_obj['location'] )
        where = "/%s/%s" % (app, model_name)

        if not self.f: # TODO make a decorator
            raise IOError('Open the backend first.')

        to_save = json.dumps( json_obj )
        to_save = np.array( to_save )

        try:
            self.f.removeNode( where, str(lid) )
        except NoSuchNodeError:
            pass

        self.f.createArray(where, str(lid), to_save)

    def save_data(self, data, location):
        """ bla foo """
        if not self.f:
            raise IOError('Open the backend first.')

        if is_permalink( location ):
            location = extract_location( location )

        where = '/datafiles'
        lid = get_id_from_permalink( location )

        try:
            self.f.removeNode( where, str(lid) )
        except NoSuchNodeError:
            pass

        self.f.createArray(where, str(lid), data)

    def delete(self, location):
        if not self.f:
            raise IOError('Open the backend first.')

        if is_permalink( location ):
            location = extract_location( location )

        app, model_name, lid = self._meta.parse_location( location )
        where = "/%s/%s" % (app, model_name)

        self.f.removeNode( where, str(lid) )


    #---------------------------------------------------------------------------
    # helper functions
    #---------------------------------------------------------------------------

    def apply_filter(self, json_objs, params):
        """ filters a given JSON objs list according to the given params. For 
        the moment just field / value filter + some lookups. Must be extended to
        support all possible cases. """

        if not json_objs:
            return []

        filters = []
        app, model_name = parse_model( json_objs[0] )
        app_definition = self._meta.app_definitions[ model_name ]

        for k, v in params.items():
            if k.find('isnull') > -1 and not (v == 0):
                v = None # dirty fix FIXME

            # lookups not implemented, clean
            if k.find('__') > -1:
                k = k[:k.find('__')]

            # treat as parent id filter
            if k in app_definition['parents']:
                json_objs = filter( lambda x: \
                    get_id_from_permalink( x['fields'][ k ] ) == v, json_objs )

            # treat as field data filter
            elif k in app_definition['data_fields'].keys():
                json_objs = filter( lambda x: \
                    x['fields'][ k ]['data'] == v, json_objs )

            elif k in ['id', 'location', 'model', 'permalink']:
                json_objs = filter( lambda x: x[ k ] == v, json_objs )

            # simple field / value filter
            else:
                json_objs = filter( lambda x: \
                    x['fields'][ k ] == v, json_objs )

        return json_objs

    #---------------------------------------------------------------------------
    # bad attempts, clean after fixing a prototype
    #---------------------------------------------------------------------------

    def _save_to_location(self, location, name, obj):
        """ saves (ovewrites if exists) a given JSON or array obj to the cache 
        file at a given location with a given name """
        if not self.f:
            raise IOError('Open the backend first.')

        try: # JSON object
            to_save = json.dumps(obj)
            to_save = np.array( to_save )

        except TypeError:
            pass # array given

        try:
            self.f.removeNode( location, name )
        except NoSuchNodeError:
            pass

        self.f.createArray(location, name, arr)


    def _save(self, obj, cascade=True): # FIXME
        """ creates/updates an object, returns updated JSON representation """
        data_refs = self.save_data( obj )
        json_obj = Serializer.serialize(obj, self._meta, data_refs)

        cls = self._meta.get_type_by_obj( obj )
        app = self._meta.app_prefix_dict[cls]
        location = json_obj['location']

        if hasattr(obj, '_gnode'): # existing object, should be in cache
            json_cached = self.get( location, f )

            if not json_cached == None:
                if json_cached == json_obj:
                    return 304 # object not modified

            # remove host from the permalink to indicate that object has changes
            json_obj['permalink'] = extract_location( json_obj['permalink'] )
            self._save_to_location(location, name, json_obj)
            return 200 # successfuly saved

        else: # new object, create
            self._save_to_location(location, name, json_obj)
            return 201 # successfully created

        # return JSON?
        # update parent children, in the cache, in memory?




    def fake_get(self, location, params={}, cascade=True, data_load=True, mode='obj'):
        """ returns a single object or it's JSON representation (mode='json')"""

        f = tb.openFile( self._meta.cache_path, "r" )
        processed = [] # collector of permalinks of processed objects
        stack = [ location ] # a stack of objects to sync

        while len( stack ) > 0:

            location = stack[0] # take first object from stack

            # 1. process core location
            json_obj = self.get( location, f )
            if json_obj == None:
                continue

            app_name, model_name, model = parse_model(json_obj)

            if mode == 'obj': # construct a python object

                data_refs = {} # is a dict like {'signal': <array...>, ...}
                if data_load:
                    for array_attr in self._meta.get_array_attr_names( model_name ):
                        arr_loc = json_obj['fields'][ array_attr ]['data']
                        data = self.get( arr_loc, f )
                        if not data == None:
                            data_refs['array_attr'] = data

                obj = Serializer.deserialize( json_obj, self._meta, data_refs )

            else: # just keep JSON representation
                obj = json_obj

            # 2. put children in the stack???
            children = self._meta.app_definitions[model_name]['children']
            if cascade and children:
                for child in children: # 'child' is like 'segment', 'event' etc.

                    field_name = child + '_set'
                    if obj._gnode['fields'].has_key( field_name ) and \
                        obj._gnode['fields'][ field_name ]:
                        rel_objs = []

                        for rel_link in obj._gnode['fields'][ field_name ]:
                            # fetching *child*-type objects
                            ch = self.pull( rel_link, params=params, data_load=data_load, _top=False )
                            rel_objs.append( ch )

                        if rel_objs: # parse children into parent attrs
                            # a way to assign kids depends on object type
                            self._assign_child( child, obj, rel_objs )
        f.close()
        return obj
