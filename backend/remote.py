import tables as tb
import numpy as np

import os
import getpass
import urlparse
import requests

from requests.exceptions import ConnectionError
from tables.exceptions import NoSuchNodeError
from utils import *
from base import BaseBackend

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
        try:
            auth = requests.post(auth_url, {'username': username, 'password': password})
            if auth.cookies:
                self.cookie = auth.cookies
                print_status( 'Authenticated at %s as %s.\n' % \
                    (self._meta.host, username) )

            else:
                print_status( 'Not connected (%s). Going offline mode.\n' % \
                    auth.status_code )

        except ConnectionError, e:
            print_status( 'Not connected (%s). Going offline mode.\n' % \
                cut_to_render(str(e)) )


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
        fid = get_id_from_permalink( location )
        url = '%s%s/%s/%s/' % (self._meta.host, "datafiles", str(fid), 'data')

        print_status('loading datafile %s from server...' % fid)

        r = requests.get(url, cookies=self.cookie)

        # download and save file to temp folder
        temp_name = str(fid) + '.h5'
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

