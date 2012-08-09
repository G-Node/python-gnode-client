#!/usr/bin/env python
import requests

import simplejson as json

from utils import load_profile, authenticate


def init(config_file='default.json', *args, **kwargs ):
    """ some easy to remember function to start g-node session """
    url, username, password = load_profile(config_file)
    return Session(url, username, password, *args, **kwargs )


class Session(object):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, url, username, password, *args, **kwargs ):
        self.url = url
        self.username = username
        self.password = password
        self.cookie_jar = authenticate(self.url, self.username,
            self.password)
        self.auth_cookie = self.cookie_jar['sessionid']
        # TODO of course make it more flexible


    def get(self, obj_type, obj_id=None, verbosity=None):
        """Get one or several objects from the server of a given object type.

        Args:
            obj_type: block, segment, event, eventarray, epoch, epocharray,
                unit, spiketrain, analogsignal, analogsignalarray,
                irsaanalogsignal, spike, recordingchannelgroup or
                recordingchannel

            obj_id: the id of the objects to retrieve as an integer or a list

            verbosity: controls the amount of information about the received objects
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

        if not verbosity:
        #TODO check that I am reading JSON from the right object
            for obj in obj_id:
                resp = requests.get(self.url+str(obejct_type)+'/'+str(
                    object_id)+'/', cookies=self.auth_cookie)
                json_obj = resp.json
                objects.append(json.loads(json_obj))
        else:
            for obj in obj_id:
                resp = requests.get(self.url+str(obejct_type)+'/'+str(
                    object_id)+'/'+'?q='+str(verbosity)+'/',
                    cookies=self.auth_cookie)
                json_obj = resp.json
                objects.append(json.loads(json_obj))

        # deserialize received JSON object
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
