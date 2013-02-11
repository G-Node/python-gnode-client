#!/usr/bin/env python
import os
import re

import requests
import simplejson as json

from utils import load_profile, authenticate
import errors
from serializer import DataDeserializer


def init(config_file='default.json'):
    """Initialize session using data specified in a JSON configuration file

    Args:
        config_file: name of the configuration file in which the profile
            to be loaded is contained the standard profile is located at
            default.json"""

    host, port, https, prefix, username, password, cache_dir = load_profile(
        config_file)

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

    return Session(url, username, password, cache_dir)


def load_saved_session(pickle_file):
    """Load a previously saved session
    """
    #TODO: finish this
    import pickle


    with open(filename, 'rb') as pkl_file:
        auth_cookie = pickle.load(pkl_file)


class Session(object):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, url, username, password, cache_dir=None):

        self.url = url
        self.username = username
        self.password = password
        #TODO: Turn this into an absolute path
        self.cache_dir = os.path.abspath(cache_dir)
        self.cookie_jar = authenticate(self.url, self.username,
            self.password)
        #the auth cookie is actually not necessary; the cookie jar should be
        #sent instead
        #self.auth_cookie = self.cookie_jar['sessionid']
        # TODO of course make it more flexible
        #TODO: figure out an elegant way to set URL stems that are often used
        # such as .../electrophysiology/, .../metadata/, etc...
        self.data_url = self.url+'electrophysiology/'
        self.files_url = self.url+'datafiles/'

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

    def get(self, obj_type, obj_id, signal_params={}):
        """Get one or several objects from the server of a given object type.

        Args:
            obj_type: block, segment, event, eventarray, epoch, epocharray,
                unit, spiketrain, analogsignal, analogsignalarray,
                irsaanalogsignal, spike, recordingchannelgroup or
                recordingchannel

            obj_id: the id of the objects to retrieve as an integer or a list

            signal_params: dictionary containing parameter values used to get
                only parts of the original object. These only work for the
                signal-based objects 'analogsignal' and 'irsaanalogsignal'.

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

        Example:
            get('analogsignal', 1, {'downsample': 100})
        """
        #accept obj_id as a single element or list (or tuple)
        if type(obj_id) is not list and type(obj_id) is not tuple:
            obj_id = [obj_id]

        objects = []

        params = signal_params

        params['q']='full'

        for obj in obj_id:
            resp = requests.get(self.data_url+str(obj_type)+'/'+str(obj)+'/',
                params=params, cookies=self.cookie_jar)
            
            if resp.status_code == 200:
                json_dict = resp.json
            else:
                raise errors.error_codes[resp.status_code]

            data_obj = DataDeserializer.deserialize(json_dict, session=self)

            objects.append(data_obj)

        #else here is the case multiple obj_ids have been requested, in which
        # case we return a list
        if len(objects) == 1:
            objects = objects[0]

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