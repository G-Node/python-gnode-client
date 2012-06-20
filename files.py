#!/usr/bin/env python
"""
Methods operating on the files stored at the data store.
"""

import requests

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