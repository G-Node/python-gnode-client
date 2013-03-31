#!/usr/bin/env python
import os
import re

import requests
import getpass
import simplejson as json

import errors
from utils import *
from serializer import Deserializer
from browser import Browser

try: 
    import simplejson as json
except ImportError: 
    import json


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

	auth = requests.post(url+'account/authenticate/', {'username': username, 'password': password})
	return auth.cookies


def load_saved_session(pickle_file):
    """Load a previously saved session
    """
    #TODO: finish this
    import pickle
    with open(filename, 'rb') as pkl_file:
        auth_cookie = pickle.load(pkl_file)

class Meta:
    """ abstract class to handle settings, auth information for Session """
    pass


class Session( Browser ):
    """ Object to handle connection and client-server data transfer """

    _cache_map = {} # map of cached objects, location: reference, like 
    # _cache_map = {
    #   'metadata/section/293847/': '5c142e1ace4bfb766dcec1995428dbd99ea057c7',
    #   'neo/block/198472/': '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f'
    # }

    _cache = {} # in-memory cache, contains objects by reference, like
    # _cache = {
    #   '5c142e1ace4bfb766dcec1995428dbd99ea057c7': <Section ...>,
    #   '16613a7b6b2fa4433a2927b6e9a0b0b63a0b419f': <Block ...>
    # }

    def __init__(self, profile_data, model_data):

        meta = Meta() # store all settings in Meta class as _meta attribute
        meta.username = profile_data['username']
        meta.password = profile_data['password']
        meta.cache_dir = os.path.abspath( profile_data['cacheDir'] )
        meta.temp_dir = os.path.abspath( profile_data['tempDir'] )
        meta.max_line_out = profile_data['max_line_out']

        meta.host = build_hostname( profile_data )
        meta.app_definitions, meta.model_names, meta.app_prefix_dict = \
            load_app_definitions(model_data)
        meta.app_aliases, meta.cls_aliases = build_alias_dicts( profile_data['alias_map'] )

        meta.cookie_jar = authenticate(meta.host, meta.username, meta.password)
        self._meta = meta

        #TODO: parse prefixData, apiDefinition, caching, DB
        # M.Pereira:
        # the auth cookie is actually not necessary; the cookie jar should be
        # sent instead
        # self.auth_cookie = meta.cookie_jar['sessionid']

    def clear_cache(self):
        """ removes all objects from the cache """
        self._cache_map = {}
        self._cache = {}

    def get(self, obj_type, id=None, params={}, cascade=True, data_load=True):
        """ Gets one or several objects from the server of a given object type.

        Args:
        obj_type: type of the object (like block, segment or section.)

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

        Examples:
        get('analogsignal', obj_id=38551, params={'downsample': 100})
        get('analogsignal', params={'segment__id': 93882, 'start_time': 500.0})
        get('section', params={'odml_type': 'experiment', 'date_created': '2013-02-22'})

        """
        # resolve alias - short model name like 'rcg' -> 'recordingchannelgroup'
        if obj_type in self._meta.cls_aliases.values():
            obj_type = [k for k, v in self._meta.cls_aliases.items() if v==obj_type][0]

        if not obj_type in self._meta.model_names:
            raise TypeError('Objects of that type are not supported.')

        objects = [] # resulting objects set
        headers = {} # request headers
        params['q'] = 'full' # always operate in full mode, see API specs
        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        url = '%s%s/%s/' % (self._meta.host, self._meta.app_prefix_dict[obj_type], str(obj_type))

        if id: # get single obj, add id to the URL
            url += str( int( id ) )

        # do fetch objects from the server
        resp = requests.get(url, params=get_params, cookies=self._meta.cookie_jar)
        raw_json = resp.json()
        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        for json_obj in raw_json['selected']:

            # 1. download attached data if needed
            data_refs = {} # collects downloaded datafile on-disk references 
            if has_data( self._meta.app_definitions, obj_type ):
                for attr in self._meta.app_definitions[obj_type]['data_fields']:
                    attr_value = json_obj['fields'][ attr ]['data']
                    if is_permalink( attr_value ):

                        if data_load:
                            # download related datafile
                            r = requests.get(attr_value, cookies=self._meta.cookie_jar)

                            temp_name = str(get_id_from_permalink(self._meta.host, attr_value)) + '.h5'
                            with open( self._meta.temp_dir + temp_name, "w" ) as f:
                                f.write( r.content )

                            # collect path to the downloaded datafile
                            data_refs[ attr ] = self._meta.temp_dir + temp_name

                        else:
                            data_refs[ attr ] = None

            # 2. parse json (+data) into python object
            obj = Deserializer.deserialize(json_obj, self, data_refs)

            objects.append(obj)

        children = self._meta.app_definitions[obj_type]['children'] # child object types
        if cascade and self._meta.app_definitions[obj_type]['children']:
            parent_ids = [obj._gnode['id'] for obj in objects]

            for child in children: # 'child' is like 'segment', 'event' etc.

                # filter to fetch objects of type child for ALL parents
                # FIXME dirty fix!! stupid data model inconsistency
                parent_name = obj_type
                if (obj_type == 'section' and child == 'section') or \
                    (obj_type == 'property' and child == 'value'):
                    parent_name = 'parent_' + parent_name

                filt = { parent_name + '__id__in': parent_ids }
                if params.has_key('at_time'): # proxy time if requested
                    filt = dict(filt, **{"at_time": params['at_time']})

                # fetching *child*-type objects
                rel_objs = self.get( child, params=filt, data_load=data_load )

                if rel_objs:
                    for obj in objects: # parse children into parent attrs
                        related = [x for x in rel_objs if \
                            getattr(x, '_gnode')[parent_name + '_id'] == obj._gnode['id']]
                        # a way to assign kids depends on object type
                        self._assign_child( child, obj, related )

        return objects

    def _assign_child(self, child, obj, related):
        """ object type-dependent parser adding children to the given obj """
        if child in ['section', 'property', 'value']:
            for rel in related:
                obj.append( rel )
        else:
            setattr(obj, child + 's', related)
        return obj




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
        del(self._meta.cookie_jar)
