#!/usr/bin/env python

import requests
import simplejson as json

import numpy as np
import quantities as pq
import neo
import os

from neo.core import *
from odml.section import BaseSection
from odml.property import BaseProperty
from odml.value import BaseValue
from errors import NotInDataStorage, NotBoundToSession, error_codes

from utils import *

units_dict = {
    'V': pq.V,
    'mV': pq.mV,
    'uV': pq.uV,
    's': pq.s,
    'ms': pq.ms,
    'us': pq.us,
    'MHz': pq.MHz,
    'kHz': pq.kHz,
    'Hz': pq.Hz,
    '1/s': pq.Hz
}

models_map = {
    'section': BaseSection,
    'property': BaseProperty,
    'value': BaseValue,
    'block': Block,
    'segment': Segment,
    'event': Event,
    'eventarray': EventArray,
    'epoch': Epoch,
    'epocharray': EpochArray,
    'unit': Unit,
    'spiketrain': SpikeTrain,
    'analogsignal': AnalogSignal,
    'analogsignalarray': AnalogSignalArray,
    'irregularlysampledsignal': IrregularlySampledSignal,
    'spike': Spike,
    'recordingchannelgroup': RecordingChannelGroup,
    'recordingchannel': RecordingChannel
}

supported_models = models_map.values()

#-------------------------------------------------------------------------------
# helper functions that depend on models
#-------------------------------------------------------------------------------

def get_type_by_obj( obj ):
    types = [k for k, v in models_map.items() if isinstance(obj, v)]
    if len(types) > 0:
        return types[0]
    return None

#-------------------------------------------------------------------------------
# common Client classes
#-------------------------------------------------------------------------------

class Meta( object ):
    """ class that handles settings, auth information etc. and some helper
    functions for backends / session manager """

    def __init__(self, profile_data, model_data):

        # init user / server info
        self.username = profile_data['username']
        self.password = profile_data['password']
        self.temp_dir = os.path.abspath( profile_data['tempDir'] )
        self.max_line_out = profile_data['max_line_out']
        self.verbose = bool( profile_data['verbose'] )
        self.host = build_hostname( profile_data )
        self.port = profile_data['port']

        # init application settings
        self.app_definitions, self.model_names, self.app_prefix_dict = \
            load_app_definitions(model_data)
        # a) app_definitions is a dict parsed from requirements.json
        # b) model names is a list like ['segment', 'event', ...]
        # c) app_prefix_dict is like 
        #       {'section': 'metadata', 'block': 'electrophysiology', ...}

        self.app_aliases, self.cls_aliases = build_alias_dicts( \
            profile_data['alias_map'] )

        # init cache settings
        self.load_cached_data = bool( profile_data['load_cached_data'] )
        self.cache_dir = os.path.abspath( profile_data['cacheDir'] )
        self.models_map = models_map

    def get_array_attr_names(self, model_name):
        """ return attr names that are arrays with ndim > 0 """
        data_fields = self.app_definitions[model_name]['data_fields']

        # FIXME dirty alternative
        names = [n for n in data_fields if n in ['times', 'durations', \
            'signal', 'waveform', 'waveforms']]

        return names

    def restore_location(self, location):
        """ restore a full version of the location using alias_map, like
        'mtd/sec/293847/' -> 'metadata/section/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self.app_aliases.items() + self.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(alias) > -1 and l[l.find(alias)-1] == '/' and \
                l[l.find(alias) + len(alias)] == '/':
                l = l.replace(alias, name)

        l = l[1:] # remove preceeding slash
        if not l.endswith('/'):
            l += '/'

        return l

    def strip_location(self, location):
        """ make a shorter version of the location using alias_map, like
        'metadata/section/293847/' -> 'mtd/sec/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self.app_aliases.items() + self.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(name) > -1 and l[l.find(name)-1] == '/' and\
                l[l.find(name) + len(name)] == '/':
                l = l.replace(name, alias)

        return l

    def parse_location(self, location):
        """ extracts app name and object type from the current location, e.g.
        'metadata' and 'section' from 'metadata/section/293847/' """
        def is_valid_id( lid ):
            try:
                int(base32int(lid))
                return True
            except ValueError:
                return False

        l = self.restore_location( location )

        res = pathlist(l)
        if not len(res) == 3:
            raise ReferenceError('Cannot parse object location %s. The format \
                should be like "metadata/section/293847/"' % str(res))


        if not res[0] in self.app_prefix_dict.values():
            raise TypeError('This app is not supported: %s' % app)
        if not res[1] in self.model_names:
            raise TypeError('This type of object is not supported: %s' % model_name)
        if not is_valid_id( res[2] ):
            raise TypeError('ID of an object must be a base32 string: %s' % lid)

        # TODO use a list for path
        return res[0], res[1], res[2]

    def clean_location(self, location):
        """ brings location to the '/metadata/section/1838/' form """
        if is_permalink( location ):
            location = extract_location( location )
        return self.restore_location( location )

    def is_modified(self, json_obj):
        """ checks if object was modified locally by validating that object
        references are permalinks """

        # 1. check permalink
        if not is_permalink( json_obj['permalink'] ):
            return True

        app_name, model_name = parse_model( json_obj )

        # 2. check data fields
        for attr in self.get_array_attr_names( model_name ):
            data = json_obj['fields'][ attr ]['data']
            if data: # should not be null
                if not is_permalink( data ):
                    return True

        # 3. check parent fields
        for attr in self.app_definitions[model_name]['parents']:
            parent = json_obj['fields'][ attr ]
            if parent: # should not be null
                if not is_permalink( parent ):
                    return True

        return False


    def get_gnode_descr(self, obj):
        """ returns G-Node JSON description assigned to a given object """
        if obj.__class__ in [BaseSection, BaseProperty, BaseValue]:
            if hasattr(obj, '_gnode'):
                return obj._gnode
        else:
            if obj.annotations.has_key('gnode'):
                return obj.annotations['gnode']
        return None

    def set_gnode_descr(self, obj, json_obj):
        """ assigns G-Node JSON description to a given object """
        if not obj.__class__ in supported_models:
            raise TypeError("This type of object is not supported %s" % str(obj))

        if obj.__class__ in [BaseSection, BaseProperty, BaseValue]:
            setattr(obj, '_gnode', json_obj)
        else:
            obj.annotations['gnode'] = json_obj


class Metadata(object):
    """ class containing metadata property-value pairs for a single object. """

    def __repr__(self):
        out = ''
        for p_name, prp in self.__dict__.items():
            property_out = cut_to_render( p_name, 20 )
            value_out = cut_to_render( str(prp.value.data) )
            out += '%s: %s\n' % ( property_out, value_out )
        return out

