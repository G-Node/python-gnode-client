#!/usr/bin/env python
"""
Methods operating on the files stored at the data store.
"""

import requests

import errors

#TODO: this definitely needs to be changed in the future!!
from utils import url

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
	perms_resp = requests.get(url+str(resource_type)+
		'/'+str(resource_id)+'/acl/', cookies=auth_cookie)	
	if perms_resp.status_code != 200:
		raise errors.error_codes[perms_resp.status_code]
	else:
		perms_data = perms_resp.json
		return perms_data['logged_in_as'],
		perms_data['safety_level'], perms_data['shared_with']

def update_permissions(auth_cookie, resource_type, resource_id,
	recursive=False, notify=False):
	"""Update a resource's permissions.

	Args:
		recursive: if resource_type == 'sections' command will be applied
			to all resources recursively. Datafiles found in subsections will
			be also updated.
		notify:
			True -- users will be notified by mail that an object was shared
			False -- no mail notification will be sent
	"""
	#TODO: figure out what can be changed
	#	shared_with ? safety_level?
	#note int(False) = 0 ; int(True) = 1
	requests.post(url+str(resource_type)+'/'+str(resource_id)+'/acl/?'+
		'cascade='+str(recursive).lower()+'&notify='+int(notify), cookies=auth_cookie)

def create_selection(auth_cookie):
	"""Create object selections
	"""
	#FIXME: input the actual selections
	requests.post(url+'/selections/', cookies=auth_cookie)

def get_list_saved_selections(auth_cookie):
	"""Get a list of the saved selections.
	"""
	#TODO: parse the response after it has been definied on the API specs
	requests.get(url+'/selections/', cookies=auth_cookie)

def get_saved_selection(auth_cookie, selection_id):
	"""Get selected objects.
	
	Args:
		selection_id: id of the object to be queried
	"""
	#TODO: parse the response after it has been definied on the API specs
	requests.get(url+'/selections/'+str(selection_id)+'/',
		cookies=auth_cookie)