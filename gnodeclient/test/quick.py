#!/usr/bin/env python

# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

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

sections = s.select(Model.SECTION, {'max_results': 5})
props = s.select(Model.PROPERTY, {'max_results': 5})
vals = s.select(Model.VALUE, {'max_results': 5})
seg = s.get("http://predata.g-node.org/electrophysiology/segment/C4FU130GIK/")
blocks = s.select(Model.BLOCK)

sig = seg.analogsignals[0]
sig = s.set(sig)


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

bl = s.get(bl.location)
if bl is None:
    print("Block deleted: OK")
else:
    print("Block deleted: FAIL")
