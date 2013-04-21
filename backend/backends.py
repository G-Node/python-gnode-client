import tables as tb
import numpy as np
import os
import requests
import getpass
import urlparse

from utils import *
from models import get_type_by_obj
from tables.exceptions import NoSuchNodeError

class BaseBackend( object ):
    """ abstract class for a client backend. Backend talks JSON + HDF5. """

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
            #if os.path.exists( self._meta.cache_path ) and \
            #    tb.isHDF5File( self._meta.cache_path ):
            #else: # init HDF5 backend
            with tb.openFile( self._meta.cache_path, 'a' ) as f:
                for model_name, app in self._meta.app_prefix_dict.items():

                    # check the app group exists
                    get_or_create( '/', app )

                    # check the model group exists
                    get_or_create( '/' + app + '/', model_name )

            print_status( 'Cache file with %s data found.\n' %  \
                sizeof_fmt( os.path.getsize( self._meta.cache_path )))

        except IOError:
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

    def get_list(self, model_name, params={}):
        """ get a list of objects of a certain type from the cache file """
        app = self._meta.app_prefix_dict[ model_name ]

        path = "/%s/%s/" % (app, model_name)

        try:
            nodes = self.f.listNodes( path )
        except NoSuchNodeError:
            return None

        json_list = []
        for node in nodes:
            json_list.append( json.loads( str(node.read()) ) )

        return json_list
        

    def get(self, location, params={}):
        """ returns a JSON or array object from the object at a given location
        in the cache file. None if not exist """
        if is_permalink( location ):
            location = urlparse.urlparse( location ).path

        try:
            node = self.f.getNode(location)
        except NoSuchNodeError:
            return None

        try: # JSON data
            obj = json.loads( str(node.read()) )

        except ValueError: # array data
            obj = np.array( node.read() )

        return obj


    def get_data(self, location):
        return self.get( location )


    def save(self, json_obj):
        """ bla foo """
        app, model_name, lid = self._meta.parse_location( json_obj['location'] )
        where = "/%s/%s/" % (app, model_name)

        if not self.f:
            raise IOError('Open the backend first.')

        to_save = json.dumps( json_obj )
        to_save = np.array( to_save )

        try:
            self.f.removeNode( where, str(lid) )
        except NoSuchNodeError:
            pass

        self.f.createArray(where, str(lid), to_save)


    def save_data(self, data, location=None):
        """ bla foo """
        if not self.f:
            raise IOError('Open the backend first.')

        if location:
            app, model_name, lid = self._meta.parse_location( location )
            where = "/%s/%s/" % (app, model_name)

        else:
            lid = get_uid()
            where = '/datafiles/'

        try:
            self.f.removeNode( where, str(lid) )
        except NoSuchNodeError:
            pass

        self.f.createArray(where, str(lid), data)

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

        cls = get_type_by_obj( obj )
        app = self._meta.app_prefix_dict[cls]
        location = json_obj['location']

        if hasattr(obj, '_gnode'): # existing object, should be in cache
            json_cached = self.get( location, f )

            if not json_cached == None:
                if json_cached == json_obj:
                    return 304 # object not modified

            # remove host from the permalink to indicate that object has changes
            json_obj['permalink'] = urlparse.urlparse( json_obj['permalink'] ).path
            self._save_to_location(location, name, json_obj)
            return 200 # successfuly saved

        else: # new object, create
            self._save_to_location(location, name, json_obj)
            return 201 # successfully created

        # return JSON?
        # update parent children, in the cache, in memory?


    def _save_data(self, obj):
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
        array_attrs = self._meta.get_array_attr_names( model_name )

        for attr in array_attrs: # attr is like 'times', 'signal' etc.

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
            init_arr = self.get( location )

            if not init_arr == None: # cached array exists
                # compare cached (original) and current data
                if np.array_equal(init_arr, curr_arr):
                    continue # no changes needed

            # 3. save as new array
            location = '/datafiles/'
            name = get_uid()
            self._save_to_location( location, name, curr_arr )

            data_refs[ attr ] = {'data': location + name + '/', 'units': units}

        return data_refs

    #---------------------------------------------------------------------------
    # bad attempts
    #---------------------------------------------------------------------------

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


class Remote( BaseBackend ):

    def __init__(self, meta):
        self._meta = meta

    #---------------------------------------------------------------------------
    # open/close backend (authenticate etc.)
    #---------------------------------------------------------------------------

    def open(self):
        """ authenticates at the REST backend """
        username = self._meta.username
        if not username:
            username = raw_input('username: ')

        password = self._meta.password
        if not password:
            password = getpass.getpass('password: ')	

        auth_url = urlparse.urljoin(self._meta.host, 'account/authenticate/')
        auth = requests.post(auth_url, {'username': username, 'password': password})
        if auth.cookies:
            print_status( 'Authenticated at %s as %s.\n' %  (self._meta.host, username) )

        self.cookie = auth.cookies

    def close(self):
        """ closes the backend """
        del(self.cookie)

    @property
    def is_active(self):
        """ is opened or not """
        return hasattr(self, 'cookie')

    #---------------------------------------------------------------------------
    # backend supported operations
    #---------------------------------------------------------------------------

    def get_list(self, model_name, params={}):
        """ get a list of objects of a certain type from the cache file """

        objects = [] # resulting objects set
        params['q'] = 'full' # always operate in full mode, see API specs
        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        url = '%s%s/%s/' % (self._meta.host, self._meta.app_prefix_dict[model_name], str(model_name))

        # do fetch list of objects from the server
        resp = requests.get(url, params=get_params, cookies=self.cookie)
        raw_json = get_json_from_response( resp )

        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        print_status('%s(s) fetched.' % model_name)
        return raw_json['selected']


    def get_data(self, location):
        """ downloads a datafile from the remote """
        lid = get_id_from_permalink( location )
        url = '%s%s/%s/%s/' % (self._meta.host, "datafiles", str(lid))

        print_status('loading datafile %s from server...' % fid)

        r = requests.get(url, cookies=self.cookie)

        # download and save file to temp folder
        temp_name = str(lid) + '.h5'
        path = os.path.join(self._meta.temp_dir, temp_name)
        with open( path, "w" ) as f:
            f.write( r.content )

        if r.status_code == 200:
            with tb.openFile(path, 'r') as f:
                carray = f.listNodes( "/" )[0]
                init_arr = np.array( carray[:] )

            print 'done.'
            return init_arr

        else:
            print 'error. file was not fetched. maybe pull again?'
            return None


    def get(self, location, params={}, etag=None):
        """ returns a JSON or array from the remote. None if not exist """
        if is_permalink( location ):
            location = extract_location( location )
        location = self._meta.restore_location( location )
        app, cls, lid = self._meta.parse_location( location )

        url = '%s%s/%s/%s/' % (self._meta.host, app, cls, str(lid))
        #params['q'] = 'full' # always operate in full mode, see API specs

        headers = {} # request headers
        if etag:
            headers['If-none-match'] = etag

        # request object from the server (with ETag)
        resp = requests.get(url, params=params, headers=headers, \
            cookies=self.cookie)

        if resp.status_code == 304: # not modified
            return 304

        else:
            # parse response json
            raw_json = get_json_from_response( resp )
            if not resp.status_code == 200:
                message = '%s (%s)' % (raw_json['message'], raw_json['details'])
                raise errors.error_codes[resp.status_code]( message )

            if not raw_json['selected']:
                raise ReferenceError('Object does not exist.')

            json_obj = raw_json['selected'][0] # should be single object 
            return json_obj


