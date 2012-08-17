#!/usr/bin/env python
import re

import requests
import simplejson as json

from utils import load_profile, authenticate, lookup_str


def init(config_file='default.json', *args, **kwargs ):
    """Initialize session using data specified in a JSON configuration file

    Args:
        config_file: name of the configuration file in which the profile
            to be loaded is contained the standard profile is located at
            default.json"""
    #TODO: parse prefixData, apiDefinition, caching, DB
    try:
        with open(str(config_file), 'r') as config_file:
            profile_data = json.load(config_file)
        
        if profile_data['port']:
            url = (profile_data['host'].strip('/')+':'+str(
                profile_data['port'])+'/'+profile_data['prefix']+'/')
        else:
            url = (profile_data['host'].strip('/')+'/'+profile_data['prefix']+'/')

        #substitute // for / in case no prefixData in the configuration file
        url = url.replace('//','/')

        #avoid double 'http://' in case user has already typed it in json file
        if profile_data['https']:
            # in case user has already typed https
            url = re.sub('https://', '', url)
            url = 'https://'+re.sub('http://', '', url)
        
        else:
            url = 'http://'+re.sub('http://', '', url)
        
        username = profile_data['username']
        password = profile_data['password']
        
    #Python3: this is the way exceptions are raised in Python 3!
    except IOError as err:
        raise errors.AbsentConfigurationFileError(err)
    except json.JSONDecodeError as err:
        raise errors.MisformattedConfigurationFileError(err)

    _is_rel_lazy = profile_data['lazyRelations']
    _is_data_lazy = profile_data['lazyData']

    return Session(url, username, password, lazy_relations=_is_rel_lazy, 
        lazy_data=_is_data_lazy, *args, **kwargs )


def load_saved_session(pickle_file):
    """Load a previously saved session
    """
    #TODO: finish this
    import pickle


    with open(filename, 'rb') as pkl_file:
        auth_cookie = pickle.load(pkl_file)


class Session(object):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, url, username, password, lazy_relations=False,
        lazy_data=False, *args, **kwargs ):
        self.url = url
        self.username = username
        self.password = password
        self.cookie_jar = authenticate(self.url, self.username,
            self.password)
        #the auth cookie is actually not necessary; the cookie jar should be
        #sent instead
        #self.auth_cookie = self.cookie_jar['sessionid']
        self._is_rel_lazy = lazy_relations
        self._is_data_lazy = lazy_data
        # TODO of course make it more flexible
        #TODO: figure out an elegant way to set URL stems that are often used
        # such as .../electrophysiology/, .../metadata/, etc...
        self.data_url = self.url+'electrophysiology/'

    def list_objects(self, object_type, params_str):
        """Get a list of objects

        Args:
            object_type: the type of NEO objects to query for (e.g.'analogsignal')
            params_str: string with search criteria constructed using function
                utils.lookup_str
        """
        #TODO: parse the JSON object received and display it in a pretty way?
        return requests.get(self.data_url+str(object_type)+'/'+params_str,
         cookies=self.cookie_jar)

    def get(self, obj_type, obj_id=None, q=None):
        """Get one or several objects from the server of a given object type.

        Args:
            obj_type: block, segment, event, eventarray, epoch, epocharray,
                unit, spiketrain, analogsignal, analogsignalarray,
                irsaanalogsignal, spike, recordingchannelgroup or
                recordingchannel

            obj_id: the id of the objects to retrieve as an integer or a list

            q: controls the amount of information about the received objects
            'link' -- just permalink
            'info' -- object with local attributes
            'beard' -- object with local attributes AND foreign keys resolved
            'data' -- data-arrays or any high-volume data associated
            'full' -- everything mentioned above
        """
        #accept obj_id as a single element or list (or tuple)
        if type(obj_id) is not list and type(obj_id) is not tuple:
            obj_id = [obj_id]

        objects = []

        if not q:
        #TODO check that I am reading JSON from the right object
            for obj in obj_id:
                resp = requests.get(self.data_url+str(obj_type)+'/'+str(
                    obj)+'/', cookies=self.cookie_jar)
                json_obj = resp.json
                objects.append(json_obj)
        else:
            for obj in obj_id:
                resp = requests.get(self.data_url+str(obj_type)+'/'+str(
                    obj)+'/'+'?q='+str(q),
                    cookies=self.cookie_jar)
                json_obj = resp.json
                objects.append(json_obj)

        # deserialize received JSON object
        if len(objects) == 1:
            objects = objects[0]
        return objects


    def create(self, obj, *kwargs):
        """Saves new object to the server """
        # serialize to JSON

        # send POST to create using API
        pass


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