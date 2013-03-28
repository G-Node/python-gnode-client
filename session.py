#!/usr/bin/env python
import os
import re

import requests
import simplejson as json

from utils import *
import errors
from serializer import Deserializer

max_line_out = 50 # max charachters to display for ls

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

    ls_filt = {} # display filters
    location = '' # current location, like 'metadata/section/293847/'
    default_view = 'section'

    def ls(self, filt=None):
        """ cmd-type ls function """
        out = '' # output
        params = dict( self.ls_filt )

        if self.location:
            app, cls, lid = self._parse_location()

            for child in self.app_definitions[ curr_type ]:
                params[ curr_type + '__id' ] = lid
                objs = self.get(child, params=params, cascade=False)
                out = self._render( objs, out )
                params.pop[ curr_type + '__id' ]
        else:
            objs = self.get(self.default_view, params=params, cascade=False)
            out = self._render( objs, out )

        print out

    def cd(self, location=''):
        """ changes the current location within the data structure """
        pass

    def _render(self, objs, out):
        """ renders a list of objects for a *nice* output """
        for obj in objs:
            # object location
            out += obj._gnode['permalink'].replace(self.url, '') + ':\t'
            # object __repr__
            out += obj.__repr__()[ : max_line_out ] + '\n'
        return out

    def _parse_location(self):
        """ extracts app name and object type from the current location, e.g.
        'metadata' and 'section' from 'metadata/section/293847/' """
        l = str( self.location )

        if l.startswith('/'):
            l = l[ 1 : ]
        if not l.endswith('/'):
            l += '/'

        res = []
        while l:
            item = l[ : l.find('/') ]
            res.append( item ) # e.g. 'metadata' or 'section'
            l = l[ len(item) + 1 : ]

        return res


class Session( Browser ):
    """ Object to handle connection and client-server data transfer """

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


    def get(self, obj_type, id=None, params={}, cascade=True):
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
        if not obj_type in self.model_names:
            raise TypeError('Objects of that type are not supported.')

        objects = []
        params['q'] = 'full' # always operate in full mode, see API specs
        url = self.url + self.app_prefix_dict[obj_type] + '/' + str(obj_type) + '/'

        if id: # get single obj, add id to the URL
            url += str( int( id ) )

        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        resp = requests.get(url, params=get_params, cookies=self.cookie_jar)
        raw_json = resp.json()
        if not resp.status_code == 200:
            raise errors.error_codes[resp.status_code](raw_json['message'])

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        for json_obj in raw_json['selected']:

            # 1. download attached data if needed
            data_refs = {} # collects downloaded datafile on-disk references 
            if has_data( self.app_definitions, obj_type ):
                for attr in self.app_definitions[obj_type]['data_fields']:
                    attr_value = json_obj['fields'][ attr ]['data']
                    if is_permalink( attr_value ):
                        # download related datafile
                        r = requests.get(attr_value, cookies=self.cookie_jar)

                        temp_name = str(get_id_from_permalink(self.url, attr_value)) + '.h5'
                        with open( self.temp_dir + temp_name, "w" ) as f:
                            f.write( r.content )

                        # collect path to the downloaded datafile
                        data_refs[ attr ] = self.temp_dir + temp_name

            # 2. parse json (+data) into python object
            obj = Deserializer.deserialize(json_obj, self, data_refs)

            objects.append(obj)

        children = self.app_definitions[obj_type]['children'] # child object types
        if cascade and self.app_definitions[obj_type]['children']:
            parent_ids = [obj._gnode['id'] for obj in objects]

            for child in children: # 'child' is like 'segment', 'event' etc.

                # filter to fetch objects of type child for ALL parents
                filt = { obj_type + '__id__in': parent_ids }
                if params.has_key('at_time'): # proxy time if requested
                    filt = dict(filt, **{"at_time": params['at_time']})

                # fetching *child*-type objects
                rel_objs = self.get( child, params=filt )

                if rel_objs:
                    for obj in objects: # parse children into parent attrs
                        setattr(obj, child + 's', [x for x in rel_objs if \
                            getattr(x, '_gnode')[obj_type + '_id'] == obj._gnode['id']])
                else:
                    for obj in objects: # no objects have children of that type
                        setattr(obj, child + 's', [])

        return objects


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
