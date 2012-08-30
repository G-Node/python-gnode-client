#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""

from .models import AnalogSignal

from quantities import mV, ms, Hz

units_dict = {'mv':mV, 'ms':ms, 'hz':Hz}

def from_json_full_to_analogsignal(json_dict):
	"""Rebuild the analogsignal object from a JSON python dictionary.
	"""
	analogsignals = []
	for s in json_dict['selected']:
		
		fields = s['fields']
		name = fields['name']
		file_origin = fields['file_origin']
		signal = fields['signal']

		signal = signal['data']
		#maps G-node server unit names to NEO unit names; usually different
		#	just by one character in lower case
		signal__units = units_dict[signal['units']]
		
		try:
			t_start = fields['t_start']['data']
			t_start__units = units_dict[fields['t_start']['units']]
		except KeyError:
			t_start = 0
			t_start__units = units_dict['ms']

		sampling_rate = fields['sampling_rate']
		sampling_rate__units = units_dict[fields]['sampling_rate']['units']]
		
		gnode_sig = AnalogSignal(signal*signal__units, t_start=t_start*
			t_start__units, sampling_rate=sampling_rate*sampling_rate__units,
			name=name, file_origin=file_origin)
		
		gnode_sig._safety_level = fields['safety_level']
		
		for a in ('permalink', 'last_modified', 'date_created', 'owner'):
			setattr(gnode_sig, a, s[a])

		for a in ('analogsignalarray', 'segment', 'recordingchannel'):
			setattr(gnode_sig, '_'+a+'_ids', s[a])
		
		analogsignals.append(gnode_sig)

		#TODO?: 'metadata', 
	if len(analogsignals) == 1:
		analogsignals = analogsignals[0]
	return analogsignals