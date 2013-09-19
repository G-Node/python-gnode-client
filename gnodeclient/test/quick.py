#!/usr/bin/env python

from gnodeclient import session

s = session.create(location="http://localhost:8000", password="pass", username="bob")
sig = s.get("/neo/analogsignal/FFRM68IOR8")
seg = sig.segment
bl = seg.block

rc = sig.recordingchannel
rcg = rc.recordingchannelgroups

repr(rcg)
str(rcg)

print str(sig.segment)
