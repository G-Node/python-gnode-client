#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""
import os

import numpy as np
import quantities as pq
import tables
import requests

import errors
from models import AnalogSignal, SpikeTrain

# core classes imports
from neo.core import *
from odml.models import Section as odmlSection
from odml.models import Property as odmlProperty
from odml.models import Value as odmlValue

units_dict = {'mv':pq.mV, 'mV':pq.mV, 'ms':pq.ms, 's':pq.s, 'hz':pq.Hz,
'Hz':pq.Hz}

models_map = {
    'metadata': {
        'section': odmlSection,
        'property': odmlProperty,
        'value': odmlValue
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
        'irsaanalogsignal': IrSaAnalogSignal,
        'spike': Spike,
        'recordingchannelgroup': RecordingChannelGroup,
        'recordingchannel': RecordingChannel
    }
}


class Deserializer(object):

	@classmethod
	def deserialize(json_obj, data={}, session):

        # 1. define a model
        model_base = json_obj['model']
        app_name = model_base[ : model_base.find('.') ]
        model_name = model_base[ model_base.find('.') + 1 : ]
        model = models_map[ app_name ][ model_name ]

        # 2. parse attrs into dict

        # 3. resolve data fields

        # 4. parse special fields

        # 5. assign self and parents ids



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
