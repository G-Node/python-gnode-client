#!/usr/bin/env python
#
# TODO?: will Gevent be necessary to handle concurrent requests?
# TODO? use r.status == 200 or check if type(r) belongs to
# 	vrequests.models.Response
# http://docs.python-requests.org/en/latest/user/install/

import re
import requests
import errors

# 'bidirectional dictionary to convert between the two nomenclatures used
#	for methos using permissions
safety_level_dict = {1: 'public', 2:'friendly', 3:'private'}


def Property(func): # FIXME what do we need it here for?
    return property(**func())


def has_data(app_definitions, model_name):
    """ checks the given model_name has data fields as per given app_definition """
    if app_definitions[ model_name ].has_key('data_fields') and \
        len(app_definitions[ model_name ]['data_fields']) > 0:
        return True
    return False


def is_permalink( link ):
    """ validates if a given link is *some* permalink """
    # add more validation here? every URL is valid..
    return str(link).find("http://") > -1


def get_id_from_permalink(host_url, permalink):
    """ parses permalink and extracts ID of the object """
    if not permalink:
        return None
    base_url = permalink.replace(host_url, '')
    return int( re.search("(?P<id>[\d]+)", base_url).group() )


def build_hostname( profile_data ):
    """ compiling actual hostname from profile parameters """

    host = profile_data['host']
    port = profile_data['port']
    https = profile_data['https']
    prefix = profile_data['prefix']

    if port:
        url = (host.strip('/')+':'+str(port)+'/'+prefix+'/')
    else:
        url = (host.strip('/')+'/'+prefix+'/')

    # substitute // for / in case no prefixData in the configuration file
    url = url.replace('//','/')

    # avoid double 'http://' in case user has already typed it in json file
    if https:
        # in case user has already typed https
        url = re.sub('https://', '', url)
        url = 'https://'+re.sub('http://', '', url)
    
    else:
        url = 'http://'+re.sub('http://', '', url)

    return url


def load_app_definitions( model_data ):
    """ reads app definitions from the model_data - structure of supported
    object models, required attributes, URL prefixes etc. """
    def parse_prefix( model ):
        if model in ['section', 'property', 'value']:
            return 'metadata'
        return 'neo'

    app_definitions = dict( model_data )
    model_names = model_data.keys()
    app_prefix_dict = dict( (model, parse_prefix( model )) for model in model_names )
   
    return app_definitions, model_names, app_prefix_dict


def build_alias_dicts( alias_map ):
    """ builds plain app/model (name) alias dicts """

    # 1. app aliases, dict like {'electrophysiology': 'mtd', ...}
    app_aliases = dict([ (app, als['alias']) for app, als in alias_map.items() ])

    # 2. model aliases, dict like {'block': 'blk', ...}
    cls_aliases = {}
    for als in alias_map.values():
        cls_aliases = dict(als['models'].items() + cls_aliases.items())

    return app_aliases, cls_aliases


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


