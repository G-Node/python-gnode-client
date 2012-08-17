#!/usr/bin/env python
"""Method(s) to reconstruct GNODE objects from JSON python dictionaries."""

from models import AnalogSignal

from quantities import mV, ms, Hz

units_dict = {'mv':mV, 'ms':ms, 'hz':Hz}

def from_full_to_analogsignal(json_dict):
	"""Rebuild the analogsignal object from a JSON python dictionary.
	"""
	analogsignals = []
	for s in json_dict['selected']:
		
		sig_fields = s['fields']
		signal = sig_fields['signal']

		sig_data = signal['data']
		#maps G-node server unit names to NEO unit names; usually different
		#	just by one character in lower case
		sig_units = units_dict[signal['units']]
		
		try:
			t_start = sig_fields['t_start']['data']
			t_start_units = units_dict[sig_fields['t_start']['units']]
		#TODO: place the right exception here for the case no t_start has been
		#	specified
		except:
			t_start = 0
			t_start_units = ms

		sampling_rate = sig_fields['sampling_rate']
		sampling_rate_units = units_dict[sig_fields]['sampling_rate']['units']]
		
		neo_sig = AnalogSignal(sig_data*sig_units, t_start=t_start*t_start_units,
			sampling_rate=sampling_rate*sampling_rate_units)
		

		analogsignals.append(neo_sig)
		

		sig.permalink = sig['permalink']

	if len(analogsignals) == 1:
		analogsignals = analogsignals[0]
	return analogsignals