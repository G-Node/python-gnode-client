#!/usr/bin/env python

from gnodeclient import session

s = session.create(password="pass", username="bob")
sig = s.get("/neo/analogsignal/FFRM68IOR8")
seg = sig.segment
bl = seg.block

rc = sig.recordingchannel
rcg = rc.recordingchannelgroup

repr(rcg)
str(rcg)

print type(sig.segment)
