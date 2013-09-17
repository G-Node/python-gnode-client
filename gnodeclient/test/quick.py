#!/usr/bin/env python

from gnodeclient import session

s = session.create(password="pass", username="bob")
c = s.get("/neo/analogsignal/FFRM68IOR8")
seg = c.segment
print type(c.segment)
