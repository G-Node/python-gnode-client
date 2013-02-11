#!/usr/bin/env python
"""
Methods operating on the data stored at the data stored

Valid NEO object types are:'block', 'segment', 'event', 'eventarray', 'epoch',
	'epocharray', 'unit', 'spiketrain', 'analogsignal', 'analogsignalarray',
	'irsaanalogsignal', 'spike', 'recordingchannelgroup', 'recordingchannel

q: controls the amount of information about the received objects
	'link' -- just permalink
	'info' -- object with local attributes
	'beard' -- object with local attributes AND foreign keys resolved
	'data' -- data-arrays or any high-volume data associated
	'full' -- everything mentioned above

'"""



import requests

from utils import url

#TODO?: break this down into several functions
def update_object(auth_cookie, object_type, json_data):
	"""Update a NEO data object. This object can also be used to create data
	objects.

	Args:
		object_type: one of the NEO object types (see header,
			module documentation)
		json: 
	"""


def get_object(auth_cookie, object_type, object_id, verbosity=None):
	"""Get a NEO data object with its attributes.

	Args:
		verbosity: controls the amount of information about the received objects
			'link' -- just permalink
			'info' -- object with local attributes
			'beard' -- object with local attributes AND foreign keys resolved
			'data' -- data-arrays or any high-volume data associated
			'full' -- everything mentioned above
	"""
	#TODO?: make this code a bit more elegant without the if clause
	#TODO: how to return the NEO object? Test how this works
	if not verbosity:
		return requests.get(url+str(obejct_type)+'/'str(object_id)+'/',
			cookies=auth_cookie)
	else:
		return requests.get(url+str(obejct_type)+'/'str(object_id)+'/'+
			'?q='+str(verbosity)+'/', cookies=auth_cookie)

def get_object_parts(auth_cookie, object_type, object_id, verbosity=None,
	cascade=False, start_time=None, end_time=None, duration=None):
	"""Get a NEO data object with its attributes.

	Args:
		verbosity: controls the amount of information about the received objects
			'link' -- just permalink
			'info' -- object with local attributes
			'beard' -- object with local attributes AND foreign keys resolved
			'data' -- data-arrays or any high-volume data associated
			'full' -- everything mentioned above
		cascade: if True, will recursively retrieve all the children objects
			(not only their permalinks). Please be careful with such requests
			as they may result in several GB of data to download.
	"""
	#TODO: which of the verbosity options is the default?
	#TODO?: make this code a bit more elegant without the if clause
	#TODO: how to return the NEO object? Test how this works
	if not verbosity:
		return requests.get(url+str(obejct_type)+'/'str(object_id)+'/',
			cookies=auth_cookie)
	else:
		return requests.get(url+str(obejct_type)+'/'str(object_id)+'/'+
			'?q='+str(verbosity)+'/', cookies=auth_cookie)

def get_list_objects(auth_cookie, object_type, params_str):
	"""Get a list of objects

	Args:
		object_type: the type of NEO objects to query for
		params_str: string with search criteria constructed using function
			utils.lookup_str
	"""
	#TODO: parse the JSON object received and display it in a pretty way?
	requests.get(url+'electrophysiology/'+str(object_type)+'/'+params_str,
		cookies=auhttp://g-node.github.com/g-node-portal/data_api/data_api_specification.htmlth_cookie)

def label_data(auth_cookie, resource_type, resource_id, metadata_urls, 
	overwrite=False):
	#TODO: add to docu which function can retrieve the metadata URLs
	"""Label one or several raw data objects with particular metadata values.
	
	Args:
		resource_type: 
		resource_id: 
		metadata_urls: a list containing urls of metadata values as attributed
			by the server. Can be retrieved using function X
	
	To completely delete existing metadata send the same request with empty
	metadata.
	"""
	#Build the JSON object
	json_data = json.dumps({'metadata': metadata_urls},sort_keys=True,
		indent=4)
	
	requests.post(url+'electrophysiology/'+str(resource_type)+'/'+
		str(resource_id)+'/', data=json_data, cookies=auth_cookie)