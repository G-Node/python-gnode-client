#!/usr/bin/env python
import os
import re

import requests
import simplejson as json

from utils import *
import errors
from serializer import Deserializer

max_line_out = 40 # max charachters to display for ls

alias_map = {
    'metadata': {
        'alias': 'mtd',
        'models': {
            'section': 'sec',
            'property': 'prp',
            'value': 'val'
        }
    },
    'electrophysiology': {
        'alias': 'eph',
        'models': {
            'block': 'blk',
            'segment': 'seg',
            'event': 'evt',
            'eventarray': 'eva',
            'epoch': 'epc',
            'epocharray': 'epa',
            'unit': 'unt',
            'spiketrain': 'spt',
            'analogsignal': 'sig',
            'analogsignalarray': 'sga',
            'irsaanalogsignal': 'ias',
            'spike': 'spk',
            'recordingchannelgroup': 'rcg',
            'recordingchannel': 'rch'
        }
    }
}

# build plain alias dicts:

# 1. app aliases, dict like {'electrophysiology': 'mtd', ...}
app_aliases = dict([ (app, als['alias']) for app, als in alias_map.items() ])

# 2. model aliases, dict like {'block': 'blk', ...}
cls_aliases = {}
for als in alias_map.values():
    cls_aliases = dict(als['models'].items() + cls_aliases.items())


def init(config_file='default.json'):
    """Initialize session using data specified in a JSON configuration file

    Args:
        config_file: name of the configuration file in which the profile
            to be loaded is contained the standard profile is located at
            default.json"""

    host, port, https, prefix, username, password, cache_dir, temp_dir = \
        load_profile( config_file )

    if port:
        url = (host.strip('/')+':'+str(port)+'/'+prefix+'/')
    else:
        url = (host.strip('/')+'/'+prefix+'/')

    #substitute // for / in case no prefixData in the configuration file
    url = url.replace('//','/')

    #avoid double 'http://' in case user has already typed it in json file
    if https:
        # in case user has already typed https
        url = re.sub('https://', '', url)
        url = 'https://'+re.sub('http://', '', url)
    
    else:
        url = 'http://'+re.sub('http://', '', url)

    return Session(url, username, password, cache_dir, temp_dir)


def load_saved_session(pickle_file):
    """Load a previously saved session
    """
    #TODO: finish this
    import pickle
    with open(filename, 'rb') as pkl_file:
        auth_cookie = pickle.load(pkl_file)


class Browser(object):
    """ abstract cls, implements cmd-type operations like ls, cd etc."""

    ls_filt = {} # dispslay filters
    location = '' # current location, like 'metadata/section/293847/'

    def ls(self, filt={}):
        """ cmd-type ls function """
        out = '' # output
        params = dict( self.ls_filt.items() + filt.items() )

        if self.location:
            app, cls, lid = self._parse_location( self.location )

            for child in self.app_definitions[ cls ]['children']:

                parent_name = cls
                # FIXME dirty fix!! stupid data model inconsistency
                if (cls == 'section' and child == 'section') or \
                    (cls == 'property' and child == 'value'):
                    parent_name = 'parent_' + parent_name

                params[ parent_name + '__id' ] = lid
                objs = self.get(child, params=params, cascade=False, data_load=False)

                out = self._render( objs, out )
                params.pop( parent_name + '__id' )
        else:
            params['parent_section__isnull'] = 1
            objs = self.get('section', params=params, cascade=False, data_load=False)
            out = self._render( objs, out )

        print out

    def cd(self, location=''):
        """ changes the current location within the data structure """
        if location == '':
            self.location = ''
            print 'back to root'

        else:
            # 1. compile url
            url = str( location )
            if is_permalink( location ):
                url = url.replace(self.url, '')
            app, cls, lid = self._parse_location( url )

            # 2. get the object at the location - raises error if not accessible
            obj = self.get(cls, id=lid, cascade=False, data_load=False)

            self.location = url
            print "entered %s" % url


    def _render(self, objs, out):
        """ renders a list of objects for a *nice* output """
        for obj in objs:

            # object location
            location = obj._gnode['permalink'].replace(self.url, '')
            out += self._strip_location(location) + '\t'

            # safety level
            out += str(obj._gnode['safety_level']) + ' '

            # object owner
            out += obj._gnode['owner'].replace(self.url, '') + '\t'

            # object __repr__
            out += obj.__repr__()[ : max_line_out ] + '\n'

        return out

    def _restore_location(self, location):
        """ restore a full version of the location using alias_map, like
        'mtd/sec/293847/' -> 'metadata/section/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        for name, alias in dict(app_aliases.items() + cls_aliases.items()).items():
            if l.find(alias) > -1 and l[l.find(alias)-1] == '/' and \
                l[l.find(alias) + len(alias)] == '/':
                l = l.replace(alias, name)

        return l

    def _strip_location(self, location):
        """ make a shorter version of the location using alias_map, like
        'metadata/section/293847/' -> 'mtd/sec/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        for name, alias in dict(app_aliases.items() + cls_aliases.items()).items():
            if l.find(name) > -1 and l[l.find(name)-1] == '/' and\
                l[l.find(name) + len(name)] == '/':
                l = l.replace(name, alias)

        return l

    def _parse_location(self, location):
        """ extracts app name and object type from the current location, e.g.
        'metadata' and 'section' from 'metadata/section/293847/' """
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

        if not len(res) == 3:
            raise ReferenceError('This location does not exist.')

        return res


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

    def __init__(self, url, username, password, cache_dir=None, temp_dir='/tmp/'):

        self.url = url
        self.username = username
        self.password = password
        #TODO: Turn this into an absolute path
        self.cache_dir = os.path.abspath(cache_dir)
        self.temp_dir = temp_dir
        self.app_definitions, self.model_names, self.app_prefix_dict = load_app_definitions()
        self.cookie_jar = authenticate(self.url, self.username,
            self.password)
        #the auth cookie is actually not necessary; the cookie jar should be
        #sent instead
        #self.auth_cookie = self.cookie_jar['sessionid']

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
        if obj_type in cls_aliases.values():
            obj_type = [k for k, v in cls_aliases.items() if v==obj_type][0]

        if not obj_type in self.model_names:
            raise TypeError('Objects of that type are not supported.')

        objects = [] # resulting objects set
        headers = {} # request headers
        params['q'] = 'full' # always operate in full mode, see API specs
        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        url = self.url + self.app_prefix_dict[obj_type] + '/' + str(obj_type) + '/'

        if id: # get single obj, add id to the URL
            url += str( int( id ) )

        # do fetch objects from the server
        resp = requests.get(url, params=get_params, cookies=self.cookie_jar)
        raw_json = resp.json()
        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        for json_obj in raw_json['selected']:

            # 1. download attached data if needed
            data_refs = {} # collects downloaded datafile on-disk references 
            if has_data( self.app_definitions, obj_type ):
                for attr in self.app_definitions[obj_type]['data_fields']:
                    attr_value = json_obj['fields'][ attr ]['data']
                    if is_permalink( attr_value ):

                        if data_load:
                            # download related datafile
                            r = requests.get(attr_value, cookies=self.cookie_jar)

                            temp_name = str(get_id_from_permalink(self.url, attr_value)) + '.h5'
                            with open( self.temp_dir + temp_name, "w" ) as f:
                                f.write( r.content )

                            # collect path to the downloaded datafile
                            data_refs[ attr ] = self.temp_dir + temp_name

                        else:
                            data_refs[ attr ] = None

            # 2. parse json (+data) into python object
            obj = Deserializer.deserialize(json_obj, self, data_refs)

            objects.append(obj)

        children = self.app_definitions[obj_type]['children'] # child object types
        if cascade and self.app_definitions[obj_type]['children']:
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
        requests.post(url, data=json.dump(json_dict), cookies=self.cookie_jar)


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
            cookies=self.cookie_jar)

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
        requests.get(self.url+'account/logout/', cookies=self.cookie_jar)
        del(self.cookie_jar)
