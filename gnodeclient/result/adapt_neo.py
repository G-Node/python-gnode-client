# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import absolute_import

import neo
from gnodeclient.result.adapt_mixins import WithLocation, WithMetadata, WithSection


class Block(WithLocation, WithMetadata, WithSection, neo.Block):
    pass


class Segment(WithLocation, WithMetadata, neo.Segment):
    pass


class EventArray(WithLocation, WithMetadata, neo.EventArray):
    pass


class Event(WithLocation, WithMetadata, neo.Event):
    pass


class EpochArray(WithLocation, WithMetadata, neo.EpochArray):
    pass


class Epoch(WithLocation, WithMetadata, neo.Epoch):
    pass


class RecordingChannelGroup(WithLocation, WithMetadata, neo.RecordingChannelGroup):
    pass


class RecordingChannel(WithLocation, WithMetadata, neo.RecordingChannel):
    pass


class Unit(WithLocation, WithMetadata, neo.Unit):
    pass


class SpikeTrain(WithLocation, WithMetadata, neo.SpikeTrain):
    pass


class Spike(WithLocation, WithMetadata, neo.Spike):
    pass


class AnalogSignalArray(WithLocation, WithMetadata, neo.AnalogSignalArray):
    pass


class AnalogSignal(WithLocation, WithMetadata, neo.AnalogSignal):
    pass


class IrregularlySampledSignal(WithLocation, WithMetadata, neo.IrregularlySampledSignal):
    pass
