#!/usr/bin/env python

from __future__ import print_function, absolute_import, division

import random
import string
import neo
import requests

from gnodeclient.model.models import Model
from gnodeclient import session

from gnodeclient.util.proxy import LazyProxy


def loader(n):
    def l():
        return "foooo"
    return l

px = LazyProxy(loader)

s = session.create(password="pass")

blocks = s.select(Model.BLOCK)

print(str(blocks[0]))
print(blocks[0].name)

for b in blocks:
    print(repr(b))
    print(str(b))

signals = s.select(Model.ANALOGSIGNAL)
loc = signals[20].location
sig = s.get(signals[20].location, refresh=True)
seg = sig.segment
bl = seg.block


print(str(sig.segment))
print(sig.segment.name)


rand_name = ''.join(random.choice(string.lowercase) for i in range(10))
print("Random name: " + rand_name)
print("Segment name: " + seg.name)
seg.name = rand_name
new_seg = s.set(seg)
print("Segment new name: " + new_seg.name)

bl = neo.Block(name="foo_block")
bl = s.set(bl)
print("Block created: " + str(bl))
print("Block location: " + bl.location)

s.delete(bl)

try:
    bl = s.get(bl.location)
except requests.exceptions.HTTPError:
    print("Block deleted: OK")
