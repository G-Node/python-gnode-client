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

#---------------------------------Utils--------------------------------------
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

#------------------------------File methods-----------------------------------

def list_datafiles(auth_cookie, lookup_str=''):
	#TODO: confirm that the ?params defined in the API are only the ones
	#defined in the lookup string definition
	return requests.get(url+'datafiles/'+lookup_str, cookies=auth_cookie)

def file_details(auth_cookie, file_id):
	return requests.get(url+'datafiles/'+str(file_id), cookies=auth_cookie)

def upload_file(auth_cookie, file_path, section_id=None, convert=1):
	"""Upload a file to the data store.

	Args:
		file_path: full path pointing to the file
		section_id: provide an ID of the section in which to store the file
			(recommended)
		convert:
			1 -- (default) try to convert the file into native format,
				if possible. Currently supported formats: neuroshare,
				ascii-csv (a csv file where every line is a signal)
			0 -- do not attempt file conversion
	"""
	params=''
	if section_id:
		params.append('section_id='+str(section_id)+'&')
	params.append('convert='+str(convert))

	requests.post(url+'datafiles/'+'?'+params, cookies=auth_cookie)

def convert_file(auth_cookie, file_id):
	"""Initiate file conversion on the server.
	"""
	requests.get(url+'datafiles/'+str(file_id)+'/convert/', cookies=auth_cookie)

def delete_file(auth_cookie, file_id, force=False):
	"""Delete file from the data store.

	Args:
		force:
			True -- delete file even if there are other users with access to
				it
			False -- file will not be deleted in the state having
				collaborators
	"""
	requests.delete(url+'datafiles/'+str(file_id)+'/?'+'force='+str(
		force).lower(), cookies=auth_cookie)

#----------------------------Permissions methods------------------------------
def get_permissions(auth_cookie, resource_type, resource_id):
	"""Get permissions for a section or data file

	Args:
		resource_type: either 'sections' or 'datafiles'
		resource_id: the id of the resource to lookup

	Output:
		logged_in_as: username used for the query
		safety_level:
			1 -- public
			2 -- friendly
			3 -- private
		shared_with: a dictionary containing username and user role id
			with the following interpretation:
			1 -- user has read permission
			2 -- user has read/write permission
	"""
	#TODO: accept also iterable objects (e.g. lists of resource_ids)
	#TODO?: use try ... except instead
	#TODO?: return meaningful strings such as public or read/write instead of
	# the codes
	#TODO?: instead of accepting resource type and object id as arguments
	# accept the url to that object
	perms_resp = requests.get(url+'resource_type/'+resource_type+
		'/'+str(resource_id)+'/acl/', cookies=auth_cookie)	
	if perms_resp.status_code != 200:
		raise errors.error_codes[perms_resp.status_code]
	else:
		perms_data = perms_response.json
		return perms_data['logged_in_as'],
		perms_data['safety_level'], perms_data['shared_with']

def update_permissions()
url, username, password = load_profile()

auth_cookie = authenticate(url, username, password)

list_data = requests.get(url+'electrophysiology/analogsignal/6/',
	cookies=auth_cookie)

list_files = requests.get(url+'datafiles/', cookies=auth_cookie)