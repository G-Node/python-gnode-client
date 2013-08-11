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
        if not os.path.exists( self.cache_dir ):
            os.mkdir( self.cache_dir )
        self.models_map = models_map

    def get_array_attr_names(self, model_name):
        """ return attr names that are arrays with ndim > 0 """
        data_fields = self.app_definitions[model_name]['data_fields']

        # FIXME dirty alternative
        names = [n for n in data_fields if n in ['times', 'durations', \
            'signal', 'waveform', 'waveforms']]

        return names

    def iterate_children(self, obj):
        """ iterator over all children of a certain object """
        cls = self.get_type_by_obj( obj )
        if not cls:
            raise "This object is not supported: %s" % str(obj)
        children = self.app_definitions[cls]['children']
        for child_type in children: # child_type is like 'segment', 'event' etc.
            for rel in getattr(obj, get_children_field_name( child_type )):
                yield rel

    def parse_location(self, location):
        return Location(location, self)

    def is_valid_id(self, lid):
        try:
            int(base32int(lid))
            return True
        except ValueError:
            return False

    def is_container(self, model_name):
        containers = ['section', 'block', 'segment', 'unit',\
            'recordingchannelgroup', 'recordingchannel']
        return model_name in containers

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

    def get_type_by_obj(self, obj):
        types = [k for k, v in self.models_map.items() if isinstance(obj, v)]
        if len(types) > 0:
            return types[0]
        return None

    def get_gnode_descr(self, obj):
        """ returns G-Node JSON description assigned to a given object """
        if hasattr(obj, '_gnode'):
            return obj._gnode
        return None

    def set_gnode_descr(self, obj, json_obj):
        """ assigns G-Node JSON description to a given object """
        if not obj.__class__ in supported_models:
            raise TypeError("This type of object is not supported %s" % str(obj))
        setattr(obj, '_gnode', json_obj)

    @property
    def mtd_classes(self):
        return [m for k, m in self.models_map.items() if k in \
            ['section', 'property', 'value']]

    @property
    def neo_classes(self):
        return [m for k, m in self.models_map.items() if k not in \
            ['section', 'property', 'value']]


class Location(list):

    def __init__(self, location, meta):
        if isinstance(location, self.__class__):
            loc = list(location)
        else:
            self._meta = meta
            loc = pathlist(location)
            if len(loc) < 3:
                raise ReferenceError('Cannot parse object location %s. The format \
                    should be like "metadata/section/293847/"' % str(loc))

            loc = self.restore_location(loc)
            if not loc[0] in self._meta.app_prefix_dict.values() + ['datafiles']:
                raise TypeError('This app is not supported: %s' % loc[0])
            if not loc[1] in self._meta.model_names + ['datafile']:
                raise TypeError('This type of object is not supported: %s' % loc[1])
            if not self._meta.is_valid_id( loc[2] ):
                raise TypeError('ID of an object must be a base32 string: %s' % loc[2])
        self.__location = loc

    def __getitem__(self, index):
        return self.__location[index]

    def __setitem__(self, key, value):
        self.__location[key] = value

    def __len__(self):
        return len(self.__location)

    def __str__(self):
        return "/" + "/".join(self.__location) + "/"

    def __repr__(self):
        return "Location(%s)" % (str(self))

    def __iter__(self):
        return iter(self.__location)

    def restore_location(self, loc):
        """ restore a full version of the location using alias_map, like
        ['mtd', 'sec', 'HTOS5G16RL'] -> ['metadata', 'section', 'HTOS5G16RL']"""
        almap = dict(self._meta.app_aliases.items() + self._meta.cls_aliases.items())
        for name, alias in almap.items():
            if loc[0] == alias: loc[0] = name
            if loc[1] == alias: loc[1] = name
        return loc

    @property
    def stripped(self):
        """ make a shorter version of the location using alias_map, like
        'metadata/section/293847/' -> 'mtd/sec/293847/' """
        loc = list(self.__location)
        almap = dict(self._meta.app_aliases.items() + self._meta.cls_aliases.items())
        for name, alias in almap.items():
            if loc[0] == name: loc[0] = alias
            if loc[1] == name: loc[1] = alias
        return "/" + "/".join(loc) + "/"


class Metadata(object):
    """ class containing metadata property-value pairs for a single object. """

    def __repr__(self):
        out = ''
        for p_name, prp in self.__dict__.items():
            property_out = cut_to_render( p_name, 20 )
            value_out = cut_to_render( str(prp.value.data) )
            out += '%s: %s\n' % ( property_out, value_out )
        return out

