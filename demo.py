#!/usr/bin/env python

#Import the function to initialize session
from session import init

#import function that will help manage request params
from utils import lookup_str

import models
import quantities as pq

#initialize session
session = init()
#type password for bob account 'pass'

#get a complete analogsignal
asig = session.get('analogsignal', 1)

#do something cool with the signal (plot, ...)

import pylab as pl
import numpy as np

pl.plot(asig.times, asig)
#TODO: how to display units without leading '1.0' ??

pl.xlabel(asig.times.units)
pl.ylabel(asig.units)

pl.show()

#show that these signals are compatible with methods operating on NEO signals
# e.g. NeuroTools

#Andrey: how to actually plot one of these new NEO signals with quantities?
# the quantity always gets on my way



#get safety level
asig.safety_level

#see with whom I have shared this data
asig.shared_with

#change safety_level
asig.set_permissions(safety_level=2)
#check permissions were changed
asig.safety_level

#log out and delete cookies
#session.shutdown()