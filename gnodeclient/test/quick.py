#!/usr/bin/env python

import random
import string

from gnodeclient.model.rest_model import Models
from gnodeclient import session

s = session.create(password="pass")

blocks = s.select(Models.BLOCK)

print str(blocks[0])
print blocks[0].name

for b in blocks:
    print repr(b)
    print str(b)

signals = s.select(Models.ANALOGSIGNAL)
loc = signals[20].location
sig = s.get(signals[20].location, refresh=True)
seg = sig.segment
bl = seg.block


print str(sig.segment)
print sig.segment.name


rand_name = ''.join(random.choice(string.lowercase) for i in range(10))
print "Random name: " + rand_name
print "Segment name: " + seg.name
seg.name = rand_name
new_seg = s.set(seg)
print "Segment new name: " + new_seg.name
