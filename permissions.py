#!/usr/bin/env python
"""
Methods operating on the files stored at the data store.
"""

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