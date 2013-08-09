import hashlib
import neo
import odml
import os
import tables as tb
import numpy as np

from utils import *

class Cache( object ):
    """ a class to handle cached objects and data for Session """

    __objs = [] # in-memory cache, contains in-memory list of objects, like
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
        self.temp_neo_path = os.path.join( self._meta.cache_dir, 'tempneo.h5' )
        self.odml_path = os.path.join( self._meta.cache_dir, 'meta.odml' )
        self.data_map_path = os.path.join( self._meta.cache_dir, 'data_map.json' )
        if meta.load_cached_data:
            self.load_cached_data()

    #---------------------------------------------------------------------------
    # USER INTERFACE functions
    #---------------------------------------------------------------------------

    def ls(self):
        out = ''
        for obj in self.objects:
            out += obj.__repr__()[ : self._meta.max_line_out ] + '\n'
        print_status( out )


    @property
    def objects(self):
        return self.__objs


    def push(self, obj, save=True):
        if not self.is_there(obj):
            self.__objs.append(obj)
                
        if save:
            self.save_objects()


    def update_data_map(self, fid, datapath):
        self.__data_map[ fid ] = datapath
        
    #---------------------------------------------------------------------------
    # WRITING TO DISK operations
    #---------------------------------------------------------------------------

    """
    def add_object(self, obj):
        json_obj = self._meta.get_gnode_descr(obj)
        if json_obj: # synced object
            if self.get_obj_by_location(json_obj['location']):
                self.save_single_object(obj)
                return None # object already cached

        self.save_single_object(o            # 4. clean-up from gnode attributes
            post_process(obj)
bj)
        self.__objs.append(obj)
    """
      
    def save_objects(self):
        """ saves all objects in the objs list """
        def pre_process(obj):
            """ tag objects with gnode attribute """
            json_obj = self._meta.get_gnode_descr(obj)
            if json_obj:
                if obj.__class__ in self._meta.mtd_classes:
                    obj.definition = json.dumps(json_obj)
                else:
                    obj.annotations['gnode'] = json_obj

            for rel in self._meta.iterate_children(obj):
                pre_process(rel)

        def post_process(obj):
            """ clean objects from gnode attribute """
            if obj.__class__ in self._meta.mtd_classes:
                obj.definition = None
            else:
                obj.annotations.pop('gnode', None)

            for rel in self._meta.iterate_children(obj):
                post_process(rel)

        iom = neo.io.hdf5io.NeoHdf5IO(filename=self.temp_neo_path)
        document = odml.Document()
        for obj in self.__objs:
            # 1. object type validation
            supp_models = [m for k, m in self._meta.models_map.items() if \
                not k in ['property', 'value']]
            if not obj.__class__ in supp_models:
                raise TypeError('Objects of that type are not supported.')

            # 2. tagging object with gnode attributes, if exists
            pre_process(obj)

            # 3. serializing
            if obj.__class__ in [self._meta.models_map['section']]: # odml object
                document.append(obj)
            else: # NEO object
                iom.save(obj)

        iom.close()
        os.rename(self.temp_neo_path, self.neo_path)
        writer = odml.tools.xmlparser.XMLWriter(document)
        writer.write_file(self.odml_path)

        # 4. clean-up from gnode attributes
        for obj in self.__objs:
            post_process(obj)



    def save_data_map(self):
        """ save file references in data_map.json """
        with open(self.data_map_path, 'w') as f:
            f.write( json.dumps(self.__data_map) )


    def save_all(self):
        """ saves all maps / objects to disk """
        self.save_data_map()
        self.save_objects()


    def clear_cache(self):
        """ removes all objects from the cache """
        self.__objs = []
        self.__data_map = {}
        self.save_all()
        # TODO clear downloaded files from disk??
                
    #---------------------------------------------------------------------------
    # READING FROM DISK operations
    #---------------------------------------------------------------------------
    
    def load_cached_data(self):
        """ loads cache from disk, validates cached files """
        def pre_process(obj):
            """ clean objects from gnode attribute """
            if obj.__class__ in self._meta.mtd_classes:
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

            for rel in self._meta.iterate_children(obj):
                pre_process(rel)

        # 1. loading data_map
        if not os.path.exists( self.data_map_path ):
            print_status('No saved data map found, downloaded files will not be used.')
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
                    print_status('Some cached files cannot be found, remove them from cache: %s\n' % to_render)

                print_status('Data map loaded (%d).\n' % len( self.__data_map.keys() ))

            except ValueError:
                print_status('Data map file cannot be parsed. Skip loading downloaded files.')

        # 2. loading NEO objects
        if not os.path.exists( self.neo_path ):
            print_status('No cached NEO map found, no objects loaded.')
        else:
            iom = neo.io.hdf5io.NeoHdf5IO(filename=self.neo_path)
            print_status( 'File with cached data found. Loading...' )

            not_found = []
            for filepath in iom._data.listNodes('/'):
                try:
                    obj = iom.get(filepath)
                    pre_process(obj)
                    self.__objs.append(obj)
                except LookupError:
                    not_found.append( filepath )
            iom.close()

            if not_found:
                to_render = str( not_found )[:100]
                print_status('Some cached data objects were damaged, remove them from cache: %s\n' % to_render)

        # 3. loading odML objects
        if not os.path.exists( self.odml_path ):
            print_status('No cached odML map found, no objects loaded.')
        else:
            document = odml.tools.xmlparser.load(self.odml_path)
            print_status( 'File with odML data found. Loading...' )

            for section in document.sections:
                pre_process(section)
                self.__objs.append(section)

        # clean _gnode properties and annotations
        print_status('Objects loaded (%d).\n' % len(self.__objs))

    #---------------------------------------------------------------------------
    # ON DISK operations with DATAFILES
    #---------------------------------------------------------------------------

    def get_data(self, location):
        """ returns a data-array from cached file on disk. None if not exist """
        location = self._meta.parse_location(location)
        fid = location[2]

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
        """ traverses cached objects tree(s) and searches for an object by 
        location, if it exists """
        def check_location(obj, location):
            json_obj = self._meta.get_gnode_descr(obj)
            if json_obj and json_obj.has_key('location'):
                curr_loc = self._meta.parse_location(json_obj['location'])
                if str(curr_loc) == str(location):
                    return obj

            for rel in self._meta.iterate_children(obj):
                found = check_location(rel, location)
                if not type(found) == type(None):
                    return found
            return None

        location = self._meta.parse_location(location)
        for obj in self.__objs:
            found = check_location(obj, location)
            if not type(found) == type(None):
                return found

        return None


    def is_there(self, original):
        """ traverses cached objects tree and searches for an equal object """
        def check_obj(obj, original):
            model_obj = self._meta.get_type_by_obj(obj)
            model_orig = self._meta.get_type_by_obj(original)
            if model_obj == model_orig and model_obj in \
                ['analogsignal', 'irregularlysampledsignal']:
                # how to f..king do that?
                comp = (obj == original)
                if comp.all():
                    return True
            else:
                try:
                    if obj == original:
                        return True
                except:
                    pass # because of NEO
                
            for rel in self._meta.iterate_children(obj):
                return check_obj(rel, original)
            return None

        for obj in self.__objs:
            return check_obj(obj, original)
        return None
        
    
    def detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        attrs_to_sync = []
        model_name = self._meta.get_type_by_obj( obj )
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


