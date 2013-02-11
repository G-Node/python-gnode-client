#!/usr/bin/env python

#Import the function to initialize session
from session import init

#import function that will help manage request params
from utils import lookup_str

import models
import quantities as pq

#initialize session
session = init('jeff.json')
#type password for bob account 'pass'

#get a complete analogsignal
asig = session.get('analogsignal', 19462, signal_params={'downsample':1000})

#do something cool with the signal (plot, ...)

import pylab as pl
import numpy as np

pl.plot(asig.times, asig)
#TODO: how to display units without leading '1.0' ??

pl.xlabel(asig.times.units)
pl.ylabel(asig.units)


#show that these signals are compatible with methods operating on NEO signals
# e.g. NeuroTools

#Andrey: how to actually plot one of these new NEO signals with quantities?
# the quantity always gets on my way

spiketr = session.get('spiketrain', 18)

#pl.plot(spiketr.times, -1.*np.ones_like(spiketr.times), marker='|',
#	linewidth=0)

#get safety level
#asig.safety_level

#see with whom I have shared this data
#asig.shared_with

#change safety_level
#asig.set_permissions(safety_level=2)
#check permissions were changed
#asig.safety_level

#log out and delete cookies
#session.shutdown()

pl.show()