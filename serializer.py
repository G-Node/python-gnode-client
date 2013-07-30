#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""
import os
import datetime
import numpy as np
import quantities as pq
import tables as tb
import requests

import errors
from utils import get_id_from_permalink, get_parent_attr_name
from models import *
from copy import deepcopy

# core classes imports
from neo.core import *


class Serializer(object):

    @classmethod
    def deserialize(cls, json_obj, meta, data_refs={}):
        """
        Instantiates a new python object from a given JSON representation.

        cls       - self

        json_obj  - a JSON representaion of the object fetched from the server.

        meta      - meta information from the current session.

        data_refs - a dict with arrays, required to instantiate new object, like 
                    {'signal': <array...>, ...}
        """

        args = [] # args to init an object
        kwargs = {} # kwargs to init an object

        # 1. define a model
        app_name, model_name = parse_model(json_obj)
        model = models_map[ model_name ]

        # 2. parse plain attrs into dict
        app_definition = meta.app_definitions[model_name]
        fields = json_obj['fields']
        for attr in app_definition['attributes']:
            if fields.has_key( attr ) and fields[ attr ]:
                kwargs[ attr ] = fields[ attr ]

        # 3. resolve data fields
        for attr in app_definition['data_fields'].keys():
            array_attrs = meta.get_array_attr_names( model_name )

            if fields.has_key( attr ) and fields[ attr ]['data']:

                if attr in array_attrs: # array-data
                    if data_refs.has_key( attr ):
                        data_value = data_refs[ attr ]

                    else: # init a dummy array for 'no-data' requests
                        data_value = np.array( [0] )

                else: # plain data field (single value)
                    data_value = fields[ attr ]['data'] 

                kwargs[ attr ] = data_value * units_dict[ fields[attr]['units'] ]

        # and some params into args for a proper init
        for argname in app_definition['init_args']: # order matters!!
            if kwargs.has_key( argname ):
                args.append( kwargs.pop( argname ) )
            else:
                args.append( None )

        # 4. init object
        obj = model( *args, **kwargs )

        # 5. adds gnode attr to the object as it's JSON representation
        meta.set_gnode_descr(obj, json_obj)

        return obj


    @classmethod
    def serialize(cls, obj, meta, data_refs={}):
        """ 
        Produces a JSON representation from a given python object.

        obj       - python object to serialize.
        meta      - meta information from the current session.
        data_refs - a dict with references to the related datafiles and units
                    {'signal': {
                            'data': '/datafiles/28374',
                            'units': 'mV'
                        },
                    ...
                    }

        serialized object should look like this:
        {
            "fields": {
                "parent_section": null,
                "odml_type": "bla",
                ...
                "property_set": [
                    "http://host/metadata/property/55"
                ],
                "is_template": false,
                "safety_level": 3,
                "block_set": [],
                "owner": "http://host/user/1",
                "date_created": "2013-04-03 15:08:15",
                "guid": "1f4a77ccc1fbd0af3e8636150e91700c629fc3ab",
                "user_custom": null,
                "name": "Perceptual evidence for saccadic updating of color stimuli"
            },
            "model": "metadata.section",
            "id": "20",
            "location": "/metadata/section/20",
            "permalink": "http://predata.g-node.org:8010/metadata/section/20"
        }
        """
        if not obj.__class__ in supported_models:
            raise TypeError('Object %s is not supported.' % \
                cut_to_render( obj.__repr__() ))

        model_name = get_type_by_obj(obj)
        app_name = meta.app_prefix_dict[ model_name ]

        if hasattr(obj, '_gnode'): # existing object
            json_obj = deepcopy(obj._gnode)

        else: # new object (never saved or synced)
            # 1. define a model
            json_obj = {'fields': {}, 'model': ''}
            json_obj['model'] = '%s.%s' % (app_name, model_name)

            # 2. define id, location and permalink OR DO NOTHING?
            #json_obj['lid'] = get_uid()
            #json_obj['location'] = "/%s/%s/%s/" % (app_name, model_name, lid)
            #json_obj['permalink'] = "/%s/%s/%s/" % (app_name, model_name, lid)

            # 3. create empty children lists
            children = meta.app_definitions[model_name]['children']
            for child in children:
                json_obj['fields'][ child + '_set' ] = []

        # 3. parse simple fields into JSON dict
        app_definition = meta.app_definitions[model_name]
        for attr in app_definition['attributes']:
            if hasattr(obj, attr) and getattr(obj, attr):
                value = Serializer._datetime_to_str( getattr(obj, attr) )
                json_obj['fields'][ attr ] = value

        # 4. parse data fields into JSON dict
        for attr in app_definition['data_fields'].keys():
            api_attr = app_definition['data_fields'][ attr ][0]
            obj_attr = app_definition['data_fields'][ attr ][2]

            if data_refs.has_key( attr ): # it's an array, use location
                if data_refs[ attr ]:
                    json_obj['fields'][ api_attr ] = data_refs[ attr ]

            else: # plain data field (single value)
                par = getattr(obj, obj_attr)
                
                if not par == None:
                    data = float( par )
                    units = Serializer.parse_units( par )
                    json_obj['fields'][ api_attr ] = \
                        {'data': data, 'units': units}

        # 5. parse parents
        for par_name in app_definition['parents']:
            attr = get_parent_attr_name( model_name, par_name )
            if hasattr(obj, attr):
                parents = getattr(obj, attr)

                is_m2m = True
                if not type(parents) == type([]):
                    parents = [ parents ]
                    is_m2m = False

                par_values = [] # collector for parent values
                for parent in parents:                
                    if not (parent == None) and hasattr(parent, '_gnode'):
                        # actual parent was synced, take his id
                        par_values.append( parent._gnode['id'] )

                if par_values:
                    if not is_m2m:
                        par_values = par_values[0]
                    json_obj['fields'][ par_name ] = par_values

                elif hasattr(obj, '_gnode') and obj._gnode['fields'].has_key(par_name):
                    # most probably object was pulled without parent, keep old 
                    # parent and do not change anything
                    json_obj['fields'][ par_name ] = obj._gnode['fields'][ par_name ]

                elif not parents:
                    # reset parent as no actual parent and obj has no parent in 
                    # memory
                    json_obj['fields'][ par_name ] = None

                else:
                    # totally skip parent as both obj and parent are not synced
                    pass

        # 6. include metadata. skip if object does not support metadata
        if hasattr(obj, 'metadata'):
            metadata = getattr(obj, 'metadata')
            if isinstance(metadata, Metadata):

                meta_refs = [prp.value._gnode['permalink'] for name, prp\
                             in metadata.__dict__.items()]
                json_obj['fields']['metadata'] = meta_refs

        # 7. validate if all required fields present - only when create?
        #missing = []
        #for attr in app_definition['required']:
        #    if not json_obj['fields'].has_key( attr ):
        #        missing.append( attr )
        #if missing:
        #    raise errors.ValidationError('The following params required for serialization: %s' % str(missing))

        return json_obj


    @classmethod
    def parse_data_permalinks(cls, json_obj, session):
        """ parses incoming JSON object representation and fetches all
        data-related permalinks """
        links = {} # dict like {'signal': 'http://host/datafiles/388109/', ...}

        app_name, model_name, model = parse_model(json_obj)
        app_definition = session._meta.app_definitions[model_name]

        if has_data( session._meta.app_definitions, model_name ):
            for attr in session._meta.app_definitions[model_name]['data_fields'].keys():
                attr_value = json_obj['fields'][ attr ]['data']
                if is_permalink( attr_value ):
                    links[ attr ] = attr_value

        return links

    @classmethod
    def update_parent_children(cls, obj, meta):
        """ when the object is synced, it's new parent relationship must be set
        into the parent object """
        model_name = get_type_by_obj(obj)
        app_definition = meta.app_definitions[model_name]
        for par_name in app_definition['parents']:
            attr = get_parent_attr_name( model_name, par_name )
            if hasattr(obj, attr):
                parents = getattr(obj, attr)

                if not type(parents) == type([]):
                    parents = [ parents ]

                for parent in parents:                
                    if parent and hasattr(parent, '_gnode'):
                        link = obj._gnode['permalink']
                        if parent._gnode['fields'].has_key( model_name + '_set' ):
                            if not link in parent._gnode['fields'][ model_name + '_set' ]:
                                parent._gnode['fields'][ model_name + '_set' ].append( link )


    @classmethod
    def parse_units(cls, element):
        match = [k for k, v in units_dict.items() if element.units == v]
        if not match:
            raise errors.UnitsError('units % are not supported. options are %s' % \
                (str(element.units), str(units_dict.keys())))
        return match[0]

    @classmethod
    def _datetime_to_str(cls, value):
        """ returns a str from a given datetime, does nothing if other type """
        if type(value) == type(datetime.date.today()):
            return value.strftime("%Y-%m-%d")

        elif type(value) == type(datetime.datetime.now()):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        else:
            return value





class DataDeserializer(object):
	"""Class of NEO data serializers"""

	@classmethod
	def deserialize(cls, json_dict, session):
		"""Meta function to deserialize any NEO data object"""
		
		s = json_dict['selected'][0]
		model = s['model']

		if model == 'neo_api.analogsignal':
			obj = cls.full_analogsignal(s, session=session)
		elif model == 'neo_api.spiketrain':
			obj = cls.full_spiketrain(s, session=session)
		else:
			raise errors.ObjectTypeNotYetSupported

		return obj


	@classmethod
	def full_analogsignal(cls, json_selected, session):
		"""Rebuild the analogsignal object from a JSON python dictionary.
		"""
		permalink = json_selected['permalink']

		fields = json_selected['fields']

		name = fields['name']
		file_origin_id = fields['file_origin']
		
		signal = fields['signal']['data']
		#maps G-node server unit names to NEO unit names; usually different
		#	just by one character in lower case
		signal__units = units_dict[fields['signal']['units']]
		
		try:
			t_start = fields['t_start']['data']
			t_start__units = units_dict[fields['t_start']['units']]
		except KeyError:
			t_start = 0.0
			t_start__units = pq.s

		sampling_rate = fields['sampling_rate']['data']
		sampling_rate__units = units_dict[fields['sampling_rate']['units']]
		
		asig = AnalogSignal(signal*signal__units, t_start=t_start*
			t_start__units, sampling_rate=sampling_rate*sampling_rate__units,
			name=name, file_origin_id=file_origin_id, permalink=permalink,
			session=session)
		
		asig._safety_level = fields['safety_level']
		
		for a in ('last_modified', 'date_created', 'owner'):
			setattr(asig, a, fields[a])

		for a in ('analogsignalarray', 'segment', 'recordingchannel'):
			setattr(asig, '_'+a+'_ids', fields[a])
			
		return asig

	@staticmethod
	def full_spiketrain(json_selected, session):
		"""Rebuild the analogsignal object from a JSON python dictionary.
		"""
		permalink = json_selected['permalink']

		fields = json_selected['fields']

		#temporary workaround waiting for Gnode to implement 'name'
		try:
			name = fields['name']
		except KeyError:
			name = ""

		file_origin_id = fields['file_origin']
		times = fields['times']['data']
		
		#maps G-node server unit names to NEO unit names; usually different
		#	just by one character in lower case
		#FIXME: Temporary workaround! The server is returning 'mV'!!
		times__units = fields['times']['units']
		if times__units in ('ms', 's'):
			times__units = units_dict[fields['times']['units']]
		elif times__units in ('mV', 'mv'):
			times__units = pq.s
		else:
			raise ValueError('Got wrong unit type for times__units')

		try:
			t_start = fields['t_start']['data']
			t_start__units = units_dict[fields['t_start']['units']]
		except KeyError:
			t_start = 0.0
			t_strart__units = pq.s

		t_stop = fields['t_stop']['data']
		t_stop__units = units_dict[fields['t_stop']['units']]
		
		if fields['waveform_set']:
			waveforms = fields['waveform_set']
		else:
			waveforms=None

		spiketr = SpikeTrain(times*times__units, t_stop=t_stop*t_stop__units,
			t_start=t_start*t_start__units, waveforms=waveforms, name=name,
			file_origin_id=file_origin_id, permalink=permalink,
			session=session)
		
		spiketr._safety_level = fields['safety_level']
		
		for a in ('last_modified', 'date_created', 'owner'):
			setattr(spiketr, a, fields[a])

		setattr(spiketr, '_'+a+'_ids', fields[a])
			
		return spiketr
