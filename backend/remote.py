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
        requests.get(self._meta.host + 'account/logout/', cookies=self.cookie)
        del(self.cookie)


    @property
    def is_active(self):
        """ is opened or not """
        return hasattr(self, 'cookie')

    #---------------------------------------------------------------------------
    # backend supported operations
    #---------------------------------------------------------------------------

    def get(self, location, params={}, etag=None):
        """ returns a JSON or array from the remote. None if not exist """
        url = '%s%s/%s/%s/' % (self._meta.host, location[0], location[1], location[2])
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

            json_obj = raw_json['selected'][0] # should be a single object 
            return json_obj


    def get_data(self, location, cache_dir=None):
        """ downloads a datafile from the remote """
        fid = location[2]
        url = '%s%s/%s/%s/' % (self._meta.host, "datafiles", str(fid), 'data')

        print_status('loading datafile %s from server...' % fid)

        r = requests.get(url, cookies=self.cookie)

        if r.status_code == 200:
            # download and save file to cache or temp folder
            file_name = str(fid) + '.h5'
            save_dir = cache_dir or self._meta.temp_dir
            path = os.path.join(save_dir, file_name)
            with open( path, "w" ) as f:
                f.write( r.content )

            try:
                with tb.openFile(path, 'r') as f:
                    carray = f.listNodes( "/" )[0]
                    init_arr = np.array( carray[:] )
            except:
                init_arr = None

            print 'done.'
            return {"id": fid, "path": path, "data": init_arr}

        else:
            message = 'error. file was not fetched. maybe pull again?'
            raise errors.error_codes[r.status_code]( message )


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


    def save(self, json_obj, force_update=False):
        """ creates / updates object at the remote """
        headers = {}
        if not force_update: # skip eTag in force_update mode
            if json_obj['fields'].has_key('guid'):
                headers = {'If-Match': json_obj['fields']['guid']}

        params = {'m2m_append': 0}

        if json_obj.has_key('location'): # existing object, update
            location = self._meta.parse_location( json_obj['location'] )
            url = '%s%s/%s/%s/' % (self._meta.host, location[0], location[1], location[2])

        else: # new object, create
            app, cls = parse_model( json_obj )
            url = '%s%s/%s/' % (self._meta.host, app, cls)

        resp = requests.post(url, data=json.dumps(json_obj), \
            headers=headers, params=params, cookies=self.cookie)

        if resp.status_code == 304:
            return 304

        if resp.status_code == 412: # location should be defined
            message = 'Object at %s was changed. please pull current version first.' % location
            raise errors.SyncFailed( message )

        raw_json = get_json_from_response( resp )
        if not resp.status_code in [200, 201]:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        return raw_json['selected'][0] # should be single object 


    def save_data(self, datapath):
        """ creates / updates object at the remote """
        if not os.path.exists( datapath ):
            raise ValueError('No file exists under a given path.')

        print_status('uploading %s...' % datapath)

        files = {'raw_file': open(datapath, 'rb')}
        url = '%s%s/' % (self._meta.host, 'datafiles')

        resp = requests.post(url, files=files, cookies=self.cookie)
        raw_json = get_json_from_response( resp )

        if not resp.status_code == 201:
            raise errors.FileUploadError('error. file upload failed: %s\nmaybe sync again?' % resp.content)

        return raw_json['selected'][0] # should be single object 


    def save_list(self, model_name, json_obj, params={}):
        """ applies changes to all available objects of a given model, filtered
        using the criterias defined in params. Changes should be represented in
        a json_obj. DOES NOT CHECK THE ETags !!! """

        params['bulk_update'] = 1
        params['m2m_append'] = 0

        app = self._meta.app_prefix_dict[ model_name ]
        url = '%s%s/%s/' % (self._meta.host, app, model_name)

        resp = requests.post(url, data=json.dumps(json_obj), \
            params=params, cookies=self.cookie)

        if resp.status_code == 304:
            return 304

        raw_json = get_json_from_response( resp )
        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        return raw_json['selected']


