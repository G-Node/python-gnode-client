#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""
import os

import numpy as np
import quantities as pq
import tables as tb
import requests

import errors
from utils import get_id_from_permalink
from models import AnalogSignal, SpikeTrain

# core classes imports
from neo.core import *
from odml.section import BaseSection
from odml.property import BaseProperty
from odml.value import BaseValue

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
    'metadata': {
        'section': BaseSection,
        'property': BaseProperty,
        'value': BaseValue
    },
    'neo_api': {
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
        'irsaanalogsignal': IrregularlySampledSignal,
        'spike': Spike,
        'recordingchannelgroup': RecordingChannelGroup,
        'recordingchannel': RecordingChannel
    }
}


class Deserializer(object):

    @classmethod
    def deserialize(cls, json_obj, session, data_refs):
        args = [] # args to init an object
        kwargs = {} # kwargs to init an object

        # 1. define a model
        model_base = json_obj['model']
        app_name = model_base[ : model_base.find('.') ]
        model_name = model_base[ model_base.find('.') + 1 : ]
        model = models_map[ app_name ][ model_name ]

        # 2. parse plain attrs into dict
        app_definition = session._meta.app_definitions[model_name]
        fields = json_obj['fields']
        for attr in app_definition['attributes']:
            if fields.has_key( attr ) and fields[ attr ]:
                kwargs[ attr ] = fields[ attr ]

        # 3. resolve data fields
        for attr in app_definition['data_fields']:
            if fields.has_key( attr ) and fields[ attr ]['data']:

                if data_refs.has_key( attr ): # extract array from datafile

                    if data_refs[ attr ]:
                        with tb.openFile(data_refs[ attr ], 'r') as f:
                            carray = f.listNodes( "/" )[0]
                            data_value = np.array( carray[:] )

                    else: # a dummy array given. request in a 'no-data' mode
                        data_value = np.array( [0] )

                else: # plain data field
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
        setattr(obj, '_gnode', {})

        # 5. parse id from permalink and save it into obj._gnode
        permalink = json_obj['permalink']
        obj_id = get_id_from_permalink(session._meta.host, permalink)
        obj._gnode['id'] = obj_id
        obj._gnode['permalink'] = permalink

        # 6. parse special fields, including ACLs into obj._gnode
        for attr in app_definition['reserved']:
            if fields.has_key( attr ):
                obj._gnode[attr] = fields[ attr ]

        # 7. assign parents permalinks/ids into obj._gnode
        for par_attr in app_definition['parents']:
            if fields.has_key( par_attr ):
                par_val = fields[ par_attr ]
                # can be multiple (m2m) -> wrap in a list if single value
                if not type(fields[ par_attr ]) == type([]):
                    par_val = [ par_val ]

                ids = []
                for v in par_val:
                    ids.append( get_id_from_permalink(session._meta.host, v) )

                if len(ids) == 1:
                    obj._gnode[par_attr + '_id'] = ids[0]
                    obj._gnode[par_attr] = par_val[0]
                else:
                    obj._gnode[par_attr + '_id'] = ids
                    obj._gnode[par_attr] = par_val

        return obj


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
