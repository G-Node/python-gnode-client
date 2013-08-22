#!/usr/bin/env python
#
# TODO?: will Gevent be necessary to handle concurrent requests?
# TODO? use r.status == 200 or check if type(r) belongs to
# 	vrequests.models.Response
# http://docs.python-requests.org/en/latest/user/install/

import re
import sys
import requests
import errors
import urlparse
import string
import random

try:
    import simplejson as json
except ImportError:
    import json

# 'bidirectional dictionary to convert between the two nomenclatures used
#	for methos using permissions
safety_level_dict = {1: 'public', 2:'friendly', 3:'private'}

# this is base32hex alphabet, used to create unique IDs
alphabet = tuple(list( '0123456789' + string.ascii_uppercase )[:32])

#-------------------------------------------------------------------------------
# Utilities
#-------------------------------------------------------------------------------

def generate_id(length=10):
    """ generates base32 string ID """
    uid = random.choice( alphabet[1:] )
    for i in range(9):
        uid += random.choice( alphabet )
    return uid


def base32str(value):
    """ converts base32 integer into the string """
    result = ''
    mask = 31
    while value > 0:
        result = alphabet[ value & mask ] + result
        value = value >> 5
    return result


def base32int(value):
    """ converts base32 string into integer """
    return long(value, 32)


def pathlist(permalink):
    """ returns a list like ['metadata', 'section', 'HTOS5G16RL'] from a given
    permalink '/metadata/section/HTOS5G16RL' """
    if not permalink:
        return None
    base_url = urlparse.urlparse(permalink).path

    if base_url[0] == "/":
        base_url = base_url[1:]
    if len(base_url) > 1 and base_url[-1] == "/":
        base_url = base_url[0: -1]

    return [i for i in base_url.split("/") if i != ""]


def is_permalink( link ):
    """ validates if a given link is *some* permalink """
    # add more validation here? every URL is valid..
    return str(link).find("http://") > -1


def get_id_from_permalink( link ):
    """ parses permalink and extracts ID of the object """
    if not link:
        return None

    if is_permalink( link ):
        link = extract_location( link )

    return pathlist(link)[2]


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

#-------------------------------------------------------------------------------
# Pretty printing
#-------------------------------------------------------------------------------

def cut_to_render( text, count=30 ):
    if len( text ) < count:
        return text
    return text[ : count-3] + '..'

def print_status(text):
    """ implements single line text output """
    sys.stdout.write( "\r\x1b[K" + text )
    sys.stdout.flush()

def sizeof_fmt( num ):
    """ byte size pretty print """
    for x in ['B','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')
    
#-------------------------------------------------------------------------------
# Parsing
#-------------------------------------------------------------------------------

def get_json_from_response( resp ):
    """ some API -> Client incoming JSON pre-processing """
    jstr = str(resp.content)
    si = 0
    while jstr.find('http://', si) > 0:
        lstart = jstr.find('http://', si)
        lend = jstr.find('"', lstart)
        link = jstr[ lstart : lend ]
        if not link.endswith('/'):
            jstr = jstr[:lend] + '/' + jstr[lend:]
        si = lend + 1

    return json.loads( jstr )


# TODO clean these all up

#-------------------------------------------------------------------------------
# Model helpers
#-------------------------------------------------------------------------------

def parse_model( json_obj ):
    """ parses incoming JSON object representation and determines model, 
    model_name and app_name """
    model_base = json_obj['model']
    app_name = model_base[ : model_base.find('.') ]
    model_name = model_base[ model_base.find('.') + 1 : ]

    return app_name, model_name

def has_data(app_definitions, model_name):
    """ checks the given model_name has data fields as per given app_definition """
    if app_definitions[ model_name ].has_key('data_fields') and \
        len(app_definitions[ model_name ]['data_fields']) > 0:
        return True
    return False

def load_app_definitions( model_data ):
    """ reads app definitions from the model_data - structure of supported
    object models, required attributes, URL prefixes etc. """
    def parse_prefix( model ):
        if model in ['section', 'property', 'value']:
            return 'metadata'
        elif model in ['datafile']:
            return 'datafiles'
        return 'electrophysiology'

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
    
def supports_metadata(cls):
    if not cls in ['section', 'property', 'value']:
        return True
    return False

def get_parent_attr_name(model_name, parent_name):
    if parent_name == 'section' and \
        (model_name == 'block' or model_name == 'datafile'):
        return parent_name
    if parent_name in ['section', 'parent_section', 'parent_property']:
        return 'parent'
    if parent_name == 'recordingchannelgroup' and model_name == 'recordingchannel':
        return 'recordingchannelgroups'
    return parent_name

def get_parent_field_name(cls, child):
    parent_name = cls
    if (cls == 'section' and child == 'section') or \
        (cls == 'property' and child == 'value'):
        parent_name = 'parent_' + parent_name
    return parent_name

def get_children_field_name(rel_type):
    if rel_type == 'property':
        return 'properties'
    if rel_type == 'irsaanalogsignal':
        return 'irregularlysampledsignals'
    return rel_type + 's'

def extract_location( permalink ):
    """ parses permalink and returns obj location, like /metadata/section/4 """
    return urlparse.urlparse( permalink ).path

#-------------------------------------------------------------------------------
# Decorators
#-------------------------------------------------------------------------------

def activate_remote(func):
    """ decorator for functions that require remote connection. opens the 
    connection if not yet opened, exits if connection fails. """
    def decorated(self, *args, **kwargs):
        if not self._remote.is_active:
            self._remote.open()

        if not self._remote.is_active:
            self._meta.logger.info('Host %s is not reachable.' % self._meta.host) 
            return None
        return func(self, *args, **kwargs)

    return decorated


def model_safe(func):
    """ decorator for functions that have model name, object or location as the
    first argument. validates first agrument is supported """
    def decorated(self, *args, **kwargs):
        first_arg = args[0] # can be model name, object or location

        if func.__name__ == 'select':
            if model_name in self._meta.cls_aliases.values():
                model_name = [k for k, v in self._meta.cls_aliases.items() if \
                    v==model_name][0]

            if not model_name in self._meta.models_map.keys():
                raise TypeError('Objects of that type are not supported.')

        # FIXME!!

        return func(self, *args, **kwargs)

    return decorated


