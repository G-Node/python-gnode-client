#!/usr/bin/env python
#
# TODO?: will Gevent be necessary to handle concurrent requests?
# TODO? use r.status == 200 or check if type(r) belongs to
# 	vrequests.models.Response
# http://docs.python-requests.org/en/latest/user/install/

import re

try: import simplejson as json
except ImportError: import json

import requests

import errors


# 'bidirectional dictionary to convert between the two nomenclatures used
#	for methos using permissions
safety_level_dict = {1: 'public', 2:'friendly', 3:'private'}


def Property(func):
    return property(**func())

def load_profile(config_file='default.json'):
    """Load Profile parameters"""
        #TODO: parse prefixData, apiDefinition, caching, DB
    try:
        with open(str(config_file), 'r') as config_file:
            profile_data = json.load(config_file)
        
        host = profile_data['host']
        port = profile_data['port']
        https = profile_data['https']
        prefix = profile_data['prefix']

        username = profile_data['username']
        password = profile_data['password']

        cache_dir = profile_data['cacheDir']
        
    #Python3: this is the way exceptions are raised in Python 3!
    except IOError as err:
        raise errors.AbsentConfigurationFileError(err)
    except json.JSONDecodeError as err:
        raise errors.MisformattedConfigurationFileError(err)

    """
    return {'host':host, 'port':port, 'https':https, 'username':username,
    'password':password, 'cache_dir':cache_dir}
    """
    return host, port, https, prefix, username, password, cache_dir

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
		import getpass
		password = getpass.getpass('password: ')	

	auth = requests.post(url+'account/authenticate/', {'username': username, 'password': password})
	return auth.cookies