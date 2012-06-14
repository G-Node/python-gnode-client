#!/usr/bin/env python
#
# TODO?: will Gevent be necessary to handle concurrent requests?
# TODO? use r.status == 200 or check if type(r) belongs to
# 	vrequests.models.Response
# http://docs.python-requests.org/en/latest/user/install/

try: import simplejson as json
except ImportError: import json

import requests

import exceptions

def load_profile(profile='default'):
	"""Initialize session using data specified on profile profile.json
	"""
	profile_data = json.load(open(str(profile)+'.json'))
	
	url = (profile_data['host'].strip('/')+':'+str(profile_data['port'])+'/'+
	       profile_data['prefix']+'/')
	url = url.replace('//','/') #substitute // for / in case of no prefixData
	#avoid double 'http://' in case user has already typed it in json file
	url = 'http://'+url.lstrip('http://')
	username = profile_data['username']
	password = profile_data['password']
	
	return url, username, password

def authenticate(url, username, password):
	"""Returns authentication cookie given username and password"""
	#TODO: ask for user input
	auth = requests.post(url, {'username': username, 'password': password})
	return auth.cookies

def shutdown(auth_cookie):
	"""Logs the user out
	"""
	#TODO: which other actions should be accomplished?
	#Notes: does not seem to be necessary to GC, close sockets, etc...
	#Requests keeps connections alive for performance increase but doesn't
	#seem to have a method to close a connection other than disabling this
	#feature all together
	#s = requests.session()
	#s.config['keep_alive'] = False
	requests.get(url+'account/logout/', cookies=auth_cookie)


def lookup_str(owner=None, safety_level=None, offset=None,
	max_results=None, q=None, **kwargs):
	"""Construct lookup strings for list requests based on user requirements.

	Args:
		safety_level (1,3): 3 for private or 1 for public items
		offset (int): useful for cases when more than 1000 results are listed
		kwargs (dict): attributes and values to lookup [TBD]
		q (str): controls the amount of information about the received objects
			'link' -- just permalink
			'info' -- object with local attributes
			'beard' -- object with local attributes AND foreign keys resolved
			'data' -- data-arrays or any high-volume data associated
			'full' -- everything mentioned above
	"""
	#TODO: add parsing of attributes with values and different lookup types
	args = locals()
	pieces = [] #different specifications to include in the lookup
	for arg, argvalue in args.items():
		if argvalue:
			pieces.append(arg+'='+str(argvalue))
	return '?'+'&'.join(pieces) if pieces else ''