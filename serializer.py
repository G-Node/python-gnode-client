#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""
import os

import numpy as np
import quantities as pq
import tables as tb
import requests

import errors
from utils import get_id_from_permalink, get_parent_attr_name
from models import *

# core classes imports
from neo.core import *


class Serializer(object):

    @classmethod
    def deserialize(cls, json_obj, session, data_refs={}, metadata=None):
        """
        Instantiates a new python object from a given JSON representation.

        cls       - self

        json_obj  - a JSON representaion of the object fetched from the server.

        session   - current user session.

        data_refs - a dict with references to the downloaded datafiles, required
                    to instantiate a new object, like 
                    {'signal': ('28374', '/tmp/28374.h5'), ...}

        metadata  - Metadata() object containing properties and values by which
                    object is tagged.
        """

        args = [] # args to init an object
        kwargs = {} # kwargs to init an object

        # 1. define a model
        model_base = json_obj['model']
        app_name = model_base[ : model_base.find('.') ]
        model_name = model_base[ model_base.find('.') + 1 : ]
        model = models_map[ model_name ]

        # 2. parse plain attrs into dict
        app_definition = session._meta.app_definitions[model_name]
        fields = json_obj['fields']
        for attr in app_definition['attributes']:
            if fields.has_key( attr ) and fields[ attr ]:
                kwargs[ attr ] = fields[ attr ]

        # 3. resolve data fields
        for attr in app_definition['data_fields'].keys():
            if fields.has_key( attr ) and fields[ attr ]['data']:

                if data_refs.has_key( attr ): # extract array from datafile

                    if data_refs[ attr ]:
                        with tb.openFile(data_refs[ attr ][1], 'r') as f:
                            carray = f.listNodes( "/" )[0]
                            data_value = np.array( carray[:] )

                    else: # init a dummy array for 'no-data' requests
                        data_value = np.array( [0] )

                else: # plain data field (single value)
                    data_value = fields[ attr ]['data'] 

                kwargs[ attr ] = data_value * units_dict[ fields[attr]['units'] ]

        # and more some params into args for a proper init
        for argname in app_definition['init_args']: # order matters!!
            if kwargs.has_key( argname ):
                args.append( kwargs.pop( argname ) )
            else:
                args.append( None )

        # 4. init object
        obj = model( *args, **kwargs )

        # 5. attach metadata if exists
        if metadata:
            setattr(obj, 'metadata', metadata) # tagged Metadata() object

        # 6. adds _gnode attr to the object as a dict with reserved attributes
        Serializer.extend(obj, json_obj, session)

        return obj

    @classmethod
    def serialize(cls, obj, session, data_refs={}, meta_refs=None):
        """ 
        Instantiates a new python object from a given JSON representation.

        obj       - python object to serialize.

        session   - current user session.

        data_refs - a dict with references to the related datafiles and units
                    {'signal': {
                            'data': http://host/datafiles/28374,
                            'units': 'mV'
                        },
                    ...
                    }

        meta_refs - list of permalinks of the related metadata values.

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
            "permalink": "http://predata.g-node.org:8010/metadata/section/20"
        }
        """
        json_obj = {'fields': {}, 'model': ''}
        if not obj.__class__ in supported_models:
            raise TypeError('Object %s is not supported.' % \
                cut_to_render( obj.__repr__() ))

        # 1. define a model
        model_name = session._get_type_by_obj(obj)
        app_name = session._meta.app_prefix_dict[ model_name ]
        json_obj['model'] = '%s.%s' % (app_name, model_name)

        # 2. put permalink if exist
        if hasattr(obj, '_gnode') and obj._gnode.has_key('permalink'):
            json_obj['permalink'] = obj._gnode['permalink']

        # 3. parse simple fields into JSON dict
        app_definition = session._meta.app_definitions[model_name]
        for attr in app_definition['attributes']:
            if hasattr(obj, attr) and getattr(obj, attr):
                json_obj['fields'][ attr ] = getattr(obj, attr)

        # 4. parse data fields into JSON dict
        for attr in app_definition['data_fields'].keys():
            api_attr = app_definition['data_fields'][ attr ][0]
            obj_attr = app_definition['data_fields'][ attr ][2]

            if data_refs.has_key( attr ): # it's an array
                json_obj['fields'][ api_attr ] = data_refs[ attr ]

            else: # plain data field (single value)
                par = getattr(obj, obj_attr)
                if par:
                    data = float( par )
                    units = [k for k, v in units_dict if par.units == v][0]
                    json_obj['fields'][ api_attr ] = \
                        {'data': data, 'units': units}

        # 5. parse parents
        for par_name in app_definition['parents']:
            attr = get_parent_attr_name( par_name )
            parent = getattr(obj, attr)
            if parent and hasattr(parent, '_gnode'):
                json_obj['fields'][ par_name ] = parent._gnode['id']
            else:
                # reset parent if parent not synchronized?
                json_obj['fields'][ par_name ] = None

        # 6. include metadata. skip if object does not support metadata
        if not meta_refs == None:
            json_obj['fields']['metadata'] = meta_refs

        return json_obj

    @classmethod
    def extend(cls, obj, json_obj, session):
        """ extends object by adding _gnode attribute as a dict with reserved 
        gnode attributes like date_created, id, safety_level etc. """
        setattr(obj, '_gnode', {}) # reserved info

        model_name = session._get_type_by_obj(obj)
        app_definition = session._meta.app_definitions[model_name]
        fields = json_obj['fields']

        # 1. parse id from permalink and save it into obj._gnode
        permalink = json_obj['permalink']
        obj_id = get_id_from_permalink(session._meta.host, permalink)
        obj._gnode['id'] = obj_id
        obj._gnode['location'] = permalink.replace(session._meta.host, '')
        obj._gnode['permalink'] = permalink

        # 2. parse special fields, including ACLs into obj._gnode
        for attr in app_definition['reserved']:
            if fields.has_key( attr ):
                obj._gnode[attr] = fields[ attr ]

        # 3. assign parents permalinks/ids into obj._gnode
        for par_attr in app_definition['parents']:
            if fields.has_key( par_attr ):

                par_val = fields[ par_attr ]

                if type( par_val ) == type([]):
                    # m2m parent, assign a list of parents
                    ids = [get_id_from_permalink(session._meta.host, v) for v in par_val]
                    obj._gnode[par_attr + '_id'] = ids
                    obj._gnode[par_attr] = par_val

                else: # single FK parent object
                    obj._gnode[par_attr + '_id'] = get_id_from_permalink(session._meta.host, par_val)
                    obj._gnode[par_attr] = par_val

        # 4. parse children permalinks into obj._gnode
        for child in app_definition['children']:
            field_name = child + '_set'
            if fields.has_key( field_name ):
                obj._gnode[ field_name ] = fields[ field_name ]

        # 5. parse data ids into obj._gnode (required to reference cache.data_map)
        for attr in app_definition['data_fields'].keys():
            if data_refs.has_key( attr ):
                if data_refs[ attr ]:
                    obj._gnode[attr + '_id'] = data_refs[ attr ][0]





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
