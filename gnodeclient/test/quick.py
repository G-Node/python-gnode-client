#!/usr/bin/env python

from gnodeclient.model.rest_model import Models
from gnodeclient import session

s = session.create()

blocks = s.select(Models.BLOCK)

print str(blocks[0])
print blocks[0].name

for b in blocks:
    print repr(b)
    print str(b)

signals = s.select(Models.ANALOGSIGNAL)
sig = s.get(signals[20].location, refresh=True)
seg = sig.segment
bl = seg.block


print str(sig.segment)
print sig.segment.name
