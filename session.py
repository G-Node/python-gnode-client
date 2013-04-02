#!/usr/bin/env python
import os, sys
import re

import requests
import getpass
import simplejson as json

import errors
from utils import *
from serializer import Serializer
from browser import Browser

try: 
    import simplejson as json
except ImportError: 
    import json

#-------------------------------------------------------------------------------
# common wrapper functions
#-------------------------------------------------------------------------------

def init(config_file='default.json', models_file='requirements.json'):
    """Initialize session using data specified in a JSON configuration files

    Args:
        config_file: name of the configuration file in which the profile
            to be loaded is contained the standard profile is located at
            default.json

        models_file: name of the configuration file defining models structure
    """

    try:
        # 1. load profile configuration
        with open(str(config_file), 'r') as f:
            profile_data = json.load(f)

        # 2. load apps and models definitions
        with open(str(models_file), 'r') as f:
            model_data = json.load(f)
        
    except IOError as err:
        raise errors.AbsentConfigurationFileError(err)
    except ValueError as err:
        raise errors.MisformattedConfigurationFileError(err)

    return Session(profile_data, model_data)


def authenticate(url, username=None, password=None):
	"""Returns authentication cookie jar given username and password"""
	#TODO: ask for user input

	#get the username if the user hasn't already specified one either by
	#directly calling the authenticate() function or by reading the username
	#and password from a configuration file (usually default.json) where these
	#have not been specified
	if not username:
		username = raw_input('username: ')

	#get the password if the user hasn't already specified one
	if not password:
		password = getpass.getpass('password: ')	

	auth = requests.post(url+'account/authenticate/', \
        {'username': username, 'password': password})
	return auth.cookies


def load_saved_session(pickle_file):
    """Load a previously saved session
    """
    #TODO: finish this
    import pickle
    with open(filename, 'rb') as pkl_file:
        auth_cookie = pickle.load(pkl_file)

#-------------------------------------------------------------------------------
# core Client classes
#-------------------------------------------------------------------------------

class Meta( object ):
    """ abstract class to handle settings, auth information for Session """
    pass


class Cache( object ):
    """ abstract class to handle cached objects and data for Session """

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


class Session( Browser ):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, profile_data, model_data):

        # 1. load meta info: store all settings in Meta class as _meta attribute
        meta = Meta()
        meta.username = profile_data['username']
        meta.password = profile_data['password']
        meta.temp_dir = os.path.abspath( profile_data['tempDir'] )
        meta.max_line_out = profile_data['max_line_out']
        meta.verbose = bool( profile_data['verbose'] )
        meta.host = build_hostname( profile_data )
        meta.app_definitions, meta.model_names, meta.app_prefix_dict = \
            load_app_definitions(model_data)
        meta.app_aliases, meta.cls_aliases = build_alias_dicts( profile_data['alias_map'] )
        meta.cookie_jar = authenticate(meta.host, meta.username, meta.password)
        self._meta = meta

        # 2. load cache
        cache_dir = os.path.abspath( profile_data['cacheDir'] ) + '/'
        load_cached_data = bool( profile_data['load_cached_data'] )
        cache_file_name = profile_data['cache_file_name']
        self._cache = Cache( cache_dir, cache_file_name, load_cached_data )

        print "Session initialized."

        #TODO: parse prefixData, apiDefinition, caching, DB
        # M.Pereira:
        # the auth cookie is actually not necessary; the cookie jar should be
        # sent instead
        # self.auth_cookie = meta.cookie_jar['sessionid']

    def clear_cache(self):
        """ removes all objects from the cache """
        self._cache.clear_cache()

    def pull(self, location, params={}, cascade=True, data_load=True, _top=True):
        """ pulls object from the specified location on the server. 
        caching:    yes
        cascade:    yes
        data_load:  yes

        _top:       reserved parameter used to detect the top function call in
                    cascade (recursive) mode. This is needed to save cache and
                    make correct printing after new objects are fetched.
        """
        if is_permalink( location ):
            location = location.replace(self._meta.host, '')
        location = self._restore_location( location )
        app, cls, lid = self._parse_location( location )

        headers = {} # request headers
        params['q'] = 'full' # always operate in full mode, see API specs

        url = '%s%s/%s/%s/' % (self._meta.host, app, cls, str(lid))

        # find object in cache
        if location in self._cache.objs_map.keys():
            headers['If-none-match'] = self._cache.objs_map[ location ]

        # request object from the server (with ETag)
        resp = requests.get(url, params=params, headers=headers, cookies=self._meta.cookie_jar)

        if resp.status_code == 304: # get object from cache
            guid = self._cache.objs_map[ location ]
            obj = self._cache.objs[ guid ]

            print_status('%s loaded from cache.' % location)

        else: # request from server

            # parse response json
            raw_json = get_json_from_response( resp )
            if not resp.status_code == 200:
                message = '%s (%s)' % (raw_json['message'], raw_json['details'])
                raise errors.error_codes[resp.status_code]( message )

            if not raw_json['selected']:
                raise ReferenceError('Object does not exist.')

            json_obj = raw_json['selected'][0] # should be single object 

            # download attached data if requested
            data_refs = self._parse_data_from_json(cls, json_obj, data_load=data_load)

            # parse json (+data) into python object
            obj = Serializer.deserialize(json_obj, self, data_refs)

            # save it to cache
            self._cache.add_object( obj )

            print_status("%s fetched from server." % location)

        children = self._meta.app_definitions[cls]['children'] # child object types
        if cascade and self._meta.app_definitions[cls]['children']:
            for child in children: # 'child' is like 'segment', 'event' etc.

                field_name = child + '_set'
                if obj._gnode.has_key( field_name ) and obj._gnode[ field_name ]:
                    rel_objs = []

                    for rel_link in obj._gnode[ field_name ]:
                        # fetching *child*-type objects
                        ch = self.pull( rel_link, params=params, data_load=data_load, _top=False )
                        rel_objs.append( ch )

                    if rel_objs: # parse children into parent attrs
                        # a way to assign kids depends on object type
                        self._assign_child( child, obj, rel_objs )

        if _top: # end of the function call if run in recursive mode
            print_status( 'Object(s) loaded.\n' )
            self._cache.save_cache() # updates on-disk cache with new objects

        return obj


    def list(self, cls, params={}, cascade=False, data_load=False, _top=True):
        """ requests objects of a given type from server in bulk mode. 
        caching:    no
        cascade:    yes
        data_load:  yes

        Args:
        cls: type of the object (like 'block', 'segment' or 'section'.)

        obj_id: id of the single object to retrieve (caching works here)

        params: dict that can contain several categories of key-value pairs:

        1. filters, like:
            'owner__username': 'robert'
            'segment__id__in': [19485,56223,89138]
            'n_definition__icontains': 'blafoo' # negative filter! (has 'n_')

        2. common params, like
            'at_time': '2013-02-22 15:34:57'
            'offset': 50
            'max_results': 20

        3. data params, to get only parts of the original object(s). These only 
            work for the data-related objects (like 'analogsignal' or 
            'spiketrain').

            start_time - start time of the required range (calculated
                using the same time unit as the t_start of the signal)
            end_time - end time of the required range (calculated using
                the same time unit as the t_start of the signal)
            duration - duration of the required range (calculated using
                the same time unit as the t_start of the signal)
            start_index - start index of the required datarange (an index
                of the starting datapoint)
            end_index - end index of the required range (an index of the
                end datapoint)
            samples_count - number of points of the required range (an
                index of the end datapoint)
            downsample - number of datapoints. This parameter is used to
                indicate whether downsampling is needed. The downsampling
                is applied on top of the selected data range using other
                parameters (if specified)

        _top:       reserved parameter used to detect the top function call in
                    cascade (recursive) mode. This is needed to save cache and
                    make correct printing after new objects are fetched.
        Examples:
        get('analogsignal', obj_id=38551, params={'downsample': 100})
        get('analogsignal', params={'segment__id': 93882, 'start_time': 500.0})
        get('section', params={'odml_type': 'experiment', 'date_created': '2013-02-22'})

        """
        # resolve alias - short model name like 'rcg' -> 'recordingchannelgroup'
        if cls in self._meta.cls_aliases.values():
            cls = [k for k, v in self._meta.cls_aliases.items() if v==cls][0]

        if not cls in self._meta.model_names:
            raise TypeError('Objects of that type are not supported.')

        objects = [] # resulting objects set
        headers = {} # request headers
        params['q'] = 'full' # always operate in full mode, see API specs
        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        url = '%s%s/%s/' % (self._meta.host, self._meta.app_prefix_dict[cls], str(cls))

        # do fetch list of objects from the server
        resp = requests.get(url, params=get_params, cookies=self._meta.cookie_jar)
        raw_json = get_json_from_response( resp )

        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        for json_obj in raw_json['selected']:

            # download attached data if requested
            data_refs = self._parse_data_from_json(cls, json_obj, data_load=data_load)

            # parse json (+data) into python object
            obj = Serializer.deserialize(json_obj, self, data_refs)

            objects.append(obj)

        print_status('%s(s) fetched.' % cls)

        # fetch children 'in bulk'
        children = self._meta.app_definitions[cls]['children'] # child object types
        if cascade and self._meta.app_definitions[cls]['children']:
            parent_ids = [obj._gnode['id'] for obj in objects]

            for child in children: # 'child' is like 'segment', 'event' etc.

                # filter to fetch objects of type child for ALL parents
                # FIXME dirty fix!! stupid data model inconsistency
                parent_name = cls
                if (cls == 'section' and child == 'section') or \
                    (cls == 'property' and child == 'value'):
                    parent_name = 'parent_' + parent_name

                filt = { parent_name + '__id__in': parent_ids }
                if params.has_key('at_time'): # proxy time if requested
                    filt = dict(filt, **{"at_time": params['at_time']})

                # fetching *child*-type objects
                rel_objs = self.list( child, params=filt, data_load=data_load, _top=False )

                if rel_objs:
                    for obj in objects: # parse children into parent attrs
                        related = [x for x in rel_objs if \
                            getattr(x, '_gnode')[parent_name + '_id'] == obj._gnode['id']]
                        # a way to assign kids depends on object type
                        self._assign_child( child, obj, related )

                # FIXME make a special processing for the Block object to avoid
                # downloading some objects twice

        if _top: # end of the function call if run in recursive mode
            #print_status( 'Object(s) loaded.\n' )
            self._cache.save_cache() # updates on-disk cache with new objects

        return objects

    #---------------------------------------------------------------------------
    # helper functions
    #---------------------------------------------------------------------------

    def _parse_data_from_json(self, cls, json_obj, data_load=True):
        """ parses incoming json object representation and fetches related 
        object data, either from cache or from the server. """
        data_refs = {} # collects downloaded datafile on-disk references 

        if has_data( self._meta.app_definitions, cls ):
            for attr in self._meta.app_definitions[cls]['data_fields']:
                attr_value = json_obj['fields'][ attr ]['data']
                if is_permalink( attr_value ):

                    fid = str(get_id_from_permalink(self._meta.host, attr_value))

                    if data_load:

                        if fid in self._cache.data_map.keys(): # get data from cache
                            data_refs[ attr ] = self._cache.data_map[ fid ]

                        else: # download related datafile

                            print_status('loading datafile %s from server...' % fid)

                            r = requests.get(attr_value, cookies=self._meta.cookie_jar)

                            temp_name = str(get_id_from_permalink(self._meta.host, attr_value)) + '.h5'
                            with open( self._cache.cache_dir + temp_name, "w" ) as f:
                                f.write( r.content )

                            # save filepath to the cache
                            self._cache.data_map[ fid ] = self._cache.cache_dir + temp_name

                            print 'datafile %s fetched from server.' % fid

                            # collect path to the downloaded datafile
                            data_refs[ attr ] = self._cache.cache_dir + temp_name

                    else:
                        data_refs[ attr ] = None

        return data_refs

    def _assign_child(self, child, obj, related):
        """ object type-dependent parser adding children to the given obj """
        if child in ['section', 'property', 'value']:
            attr_name = child + 's'
            if child == 'property':
                attr_name = 'properties'
            for rel in related:
                if not rel in getattr(obj, attr_name): # avoid duplicates
                    obj.append( rel )
        else:
            setattr(obj, child + 's', related) # raplace all
        return obj

    def _restore_location(self, location):
        """ restore a full version of the location using alias_map, like
        'mtd/sec/293847/' -> 'metadata/section/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self._meta.app_aliases.items() + self._meta.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(alias) > -1 and l[l.find(alias)-1] == '/' and \
                l[l.find(alias) + len(alias)] == '/':
                l = l.replace(alias, name)

        l = l[1:] # remove preceeding slash
        if not l.endswith('/'):
            l += '/'

        return l

    def _strip_location(self, location):
        """ make a shorter version of the location using alias_map, like
        'metadata/section/293847/' -> 'mtd/sec/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self._meta.app_aliases.items() + self._meta.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(name) > -1 and l[l.find(name)-1] == '/' and\
                l[l.find(name) + len(name)] == '/':
                l = l.replace(name, alias)

        return l

    def _parse_location(self, location):
        """ extracts app name and object type from the current location, e.g.
        'metadata' and 'section' from 'metadata/section/293847/' """
        def is_valid_id( lid ):
            try:
                int( lid )
                return True
            except ValueError:
                return False

        l = self._restore_location( location )

        if l.startswith('/'):
            l = l[ 1 : ]
        if not l.endswith('/'):
            l += '/'

        res = []
        while l:
            item = l[ : l.find('/') ]
            res.append( item ) # e.g. 'metadata' or 'section'
            l = l[ len(item) + 1 : ]

        try:
            app, cls, lid = res
        except ValueError:
            raise ReferenceError('Cannot parse object location %s. The format \
                should be like "metadata/section/293847/"' % str(res))

        if not app in self._meta.app_prefix_dict.values():
            raise TypeError('This app is not supported: %s' % app)
        if not cls in self._meta.model_names:
            raise TypeError('This type of object is not supported: %s' % cls)
        if not is_valid_id( lid ):
            raise TypeError('ID of an object must be of "int" type: %s' % lid)

        return app, cls, int(lid)


    def save(self, obj, *kwargs):
        """ Saves or updates object to the server """
        # serialize to JSON

        if obj.permalink:
            url = obj.permalink +'/'

        else:
            url = self.data_url+obj.obj_type+'/'

        json_dict = None
        #TODO: serialize object
        requests.post(url, data=json.dump(json_dict), cookies=self._meta.cookie_jar)


    def list_objects(self, object_type, params=None):
        """Get a list of objects

        Args:
            object_type: the type of NEO objects to query for (e.g.'analogsignal')
            params: a dictionary containing parameters to restrict the search
                safety_level (1,3): 3 for private or 1 for public items
                offset (int): useful for cases when more than 1000 results are listed
                q (str): controls the amount of information about the received objects
                    'link' -- just permalink
                    'info' -- object with local attributes
                    'beard' -- object with local attributes AND foreign keys resolved
                    'data' -- data-arrays or any high-volume data associated
                    'full' -- everything mentioned above

        Example call: list_objects('analogsignal', {'safety_level': '3','q': 'link'})
        """
        #TODO: parse the JSON object received and display it in a pretty way?
        resp = requests.get(self.data_url+str(object_type)+'/', params=params,
            cookies=self._meta.cookie_jar)

        if resp.status_code == 200:
            return resp.json
        else:
            raise errors.error_codes[resp.status_code]


    def bulk_update(self, obj_type, *kwargs):
        """ update several homogenious objects on the server """
        pass


    def delete(self, obj_type, obj_id=None, *kwargs):
        """ delete (archive) one or several objects on the server """
        pass

    def save_session(self, filename):
        """Save the data necessary to restart current session (cookies, etc..)
        """
        import pickle

    def shutdown(self):
        """Log out.
        """
        #TODO: which other actions should be accomplished?
        #Notes: does not seem to be necessary to GC, close sockets, etc...
        #Requests keeps connections alive for performance increase but doesn't
        #seem to have a method to close a connection other than disabling this
        #feature all together
        #s = requests.session()
        #s.config['keep_alive'] = False
        requests.get(self._meta.host+'account/logout/', cookies=self._meta.cookie_jar)
        self._cache.save_cache()
        del(self._meta.cookie_jar)



