from utils import *

import neo
import odml
import os
import tables as tb
import numpy as np

class Cache( object ):
    """ a class to handle cached objects and data for Session """

    __objs = {} # in-memory cache, contains in-memory list of objects, like
    # __objs = [
    #   <Section ...>,
    #   <Section ...>,
    #   <Block ...>
    # ]

    __data_map = {} # map of downloaded files, contains file paths by ID, like
    # __data_map = {
    #   'MAM4O5B431': '/.cache/MAM4O5B431.h5',
    #   'IKU354JH1L': '/.cache/IKU354JH1L.h5',
    # }

    def __init__(self, meta):
        self._meta = meta
        self.neo_path = os.path.join( self._meta.cache_dir, 'neo.h5' )
        self.odml_path = os.path.join( self._meta.cache_dir, 'meta.odml' )
        self.data_map_path = os.path.join( self._meta.cache_dir, 'data_map.json' )
        if meta.load_cached_data:
            self.load_cached_data()

    #---------------------------------------------------------------------------
    # ON DISK operations with OBJECTS
    #---------------------------------------------------------------------------

    def add_object(self, obj):
        """ adds object to cache map + saves it to the cache HDF5 file """
        json_obj = self._meta.get_gnode_descr(obj)
        if json_obj: # synced object
            if self.get_obj_by_location(json_obj['location']):
                return None # object already cached

        self.save_single_object(obj)
        self.__objs.append(obj)


    def save_objects(self):
        """ saves all objects in the objs list """
        for obj in self.__objs:
            self.save_single_object(obj)


    def save_single_object(self, obj):
        """ uses NeoHDF5IO to store a given object in the root (cascade!!) """

        def pre_process(obj):
            """ tag objects with gnode attribute """
            json_obj = self._meta.get_gnode_descr(obj)
            if json_obj:
                if obj.__class__ in [BaseSection, BaseProperty, BaseValue]:
                    obj.definition = json.dumps(json_obj)
                else:
                    if obj.annotations['gnode'] = json_obj

            cls = get_type_by_obj( obj )
            children = self._meta.app_definitions[cls]['children']
            for child in children: # 'child' is like 'segment', 'event' etc.
                for rel in getattr(obj, get_children_field_name( child )):
                    pre_process(rel)


        def post_process(obj):
            """ clean objects from gnode attribute """
            if obj.__class__ in [BaseSection, BaseProperty, BaseValue]:
                obj.definition = None
            else:
                obj.annotations.pop('gnode', None)

            cls = get_type_by_obj( obj )
            children = self._meta.app_definitions[cls]['children']
            for child in children: # 'child' is like 'segment', 'event' etc.
                for rel in getattr(obj, get_children_field_name( child )):
                    post_process(rel)

        # 1. object type validation
        supp_models = [m for k, m in models_map.items() if \
            not k in ['property', 'value']]
        if not obj_to_sync.__class__ in supp_models:
            raise TypeError('Objects of that type are not supported.')

        # 2. preprocessing
        pre_process(obj)

        # 3. serializing
        if obj.__class__ in [BaseSection] # odml object
            document = odml.tools.xmlparser.load(self.odml_path)
            document.append(obj)
            writer = XMLWriter(document)
            writer.write_file(self.odml_path)

        else: # NEO object
            iom = neo.io.hdf5io.NeoHdf5IO(filename=self.neo_path)
            iom.save(obj)
            iom.close()

        # 4. clean-up
        post_process(obj)


    def load_cached_data(self):
        """ loads cache from disk, validates cached files """
        def pre_process(obj):
            """ clean objects from gnode attribute """
            if obj.__class__ in [BaseSection, BaseProperty, BaseValue]:
                try:
                    json_obj = json.loads(obj.definition)
                    if type(json_obj) == type({}) and json_obj.has_key('id'):
                        self._meta.set_gnode_descr(obj, json_obj)
                        obj.definition = None
                except:
                    pass
            else:
                json_obj = obj.annotations.pop('gnode', None)
                if type(json_obj) == type({}) and json_obj.has_key('id'):
                    self._meta.set_gnode_descr(obj, json_obj)

            cls = get_type_by_obj( obj )
            children = self._meta.app_definitions[cls]['children']
            for child in children: # 'child' is like 'segment', 'event' etc.
                for rel in getattr(obj, get_children_field_name( child )):
                    pre_process(rel)

        # 1. loading data_map
        if not os.path.exists( self.data_map_path ):
            print 'No saved data map found, downloaded files will not be used.'
        else:
            try:
                with open(self.data_map_path, 'r') as f:
                    data_map = json.load(f)
                print_status( 'Data map file found. Loading...' )
                
                not_found = []
                for lid, filepath in data_map.items():
                    if os.path.exists( filepath ):
                        self.__data_map[ lid ] = filepath
                    else:
                        not_found.append( filepath )
                if not_found:
                    to_render = str( not_found )[:100]
                    print 'Some cached files cannot be found, remove them from cache: %s' % to_render

                print 'Data map loaded (%d).' % len( self.__data_map.keys() )

            except ValueError:
                print 'Data map file cannot be parsed. Skip loading downloaded files.'

        # 2. loading NEO objects
        if not os.path.exists( self.neo_path ):
            print 'No cached NEO map found, no objects loaded.'
        else:
            iom = neo.io.hdf5io.NeoHdf5IO(filename=self.neo_path)
            print_status( 'File with cached data found. Loading...' )

            not_found = []
            for filepath in iom._data.listNodes('/'):
                try:
                    obj = iom.get(filepath)
                    pre_process(obj)
                    self.__objs.append(obj)
                except:
                    not_found.append( filepath )

            if not_found:
                to_render = str( not_found )[:100]
                print 'Some cached data objects were damaged, remove them from cache: %s' % to_render

        # 3. loading odML objects
        if not os.path.exists( self.odml_path ):
            print 'No cached odML map found, no objects loaded.'
        else:
            document = odml.tools.xmlparser.load(self.odml_path)
            for section in document.sections:
                pre_process(section)
                self.__objs.append(section)

        # clean _gnode properties and annotations
        print 'Objects loaded (%d).' % len( self.__objs.keys() )


    def update_data_map(self, fid, datapath):
        self.__data_map[ fid ] = datapath


    def save_data_map(self):
        """ save file references in data_map.json """
        with open(self._meta.data_map_path, 'w') as f:
            f.write( json.dumps(self.__data_map) )


    def save_all(self):
        """ saves all maps / objects to disk """
        self.save_data_map()
        self.save_objects()


    def clear_cache(self):
        """ removes all objects from the cache """
        self.__objs = {}
        self.__data_map = {}
        self.save_all()
        # TODO clear downloaded files from disk??

    #---------------------------------------------------------------------------
    # ON DISK operations with DATAFILES
    #---------------------------------------------------------------------------

    def get_data(self, location):
        """ returns a data-array from cached file on disk. None if not exist """
        fid = str( get_id_from_permalink( location ) )

        if not self.__data_map.has_key( fid ):
            return None

        with tb.openFile( self.__data_map[ fid ], 'r') as f:
            carray = f.listNodes( "/" )[0]
            data = np.array( carray[:] )

        return {"id": fid, "path": self.__data_map[ fid ], "data": data}


    def save_data(self, arr):
        """ saves a given array to the cache_dir as HDF5 file """
        cache_dir = self._meta.cache_dir
        temp_name = hashlib.sha1( arr ).hexdigest()
        datapath = os.path.join(cache_dir, temp_name + '.h5')
        with tb.openFile( datapath, "w" ) as f:
            f.createArray('/', 'gnode_array', arr)

        return datapath

    #---------------------------------------------------------------------------
    # IN MEMORY operations
    #---------------------------------------------------------------------------

    def get_obj_by_location(self, location):
        """ traverses cached objects tree(s) and searches for an object """
        return None


    def detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        attrs_to_sync = []
        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( model_name )

        json_obj = self._meta.get_gnode_descr(obj)
        if json_obj == None:
            return data_attrs # object is new, all data attrs must be saved

        for attr in data_attrs:

            data_value = json_obj['fields'][ attr ]['data']

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


