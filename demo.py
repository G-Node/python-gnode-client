#!/usr/bin/env python

#Import the function to initialize session
from session import init

#import function that will help manage request params
from utils import lookup_str

import models
import quantities as pq

#initialize session
session = init()
#type password

asig = models.AnalogSignal([1,2,3]*pq.mV, sampling_rate=1000*pq.Hz)
setattr(asig, '_permalink_perms', 'http://141.84.42.103:8003/electrophysiology/analogsignal/1/acl/')
setattr(asig, 'permalink', 'http://141.84.42.103:8003/electrophysiology/analogsignal/1/')
setattr(asig, '_session', session)

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