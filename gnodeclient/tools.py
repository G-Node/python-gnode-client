# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
This module defines some utility functions that provide implementations for
some common procedures.
"""

from __future__ import print_function, absolute_import, division

import copy
import neo
from odml.section import BaseSection

from gnodeclient import Session


def delete_all(session, entities):
    """
    Delete a list of entities.

    :param session:
    :type session: Session
    :param entities:
    :type entities: list

    :returns: A list of deleted objects.
    :rtype: list
    """
    for ent in entities:
        if hasattr(ent, "location"):
            deleted = []
            try:
                session.delete(ent)
                deleted.append(ent)
            except RuntimeError as e:
                # TODO logging
                pass


def upload_odml_tree(session, section):
    """
    Upload a whole odml tree.

    :param session:
    :type session: Session
    :param section:
    :type section: BaseSection

    :return: The root of the uploaded odml tree.
    :rtype: BaseSection
    """
    created_objects = []

    # closure that is used for recursive upload
    def upload_section_recursive(section, parent):
        sec_uploaded = session.set(section)
        created_objects.append(sec_uploaded)

        if parent is not None:
            parent.append(sec_uploaded)
            sec_uploaded = session.set(sec_uploaded)

        for prop in section.properties:
            prop = copy.deepcopy(prop)
            sec_uploaded.append(prop)

            prop_uploaded = session.set(prop)
            created_objects.append(prop_uploaded)

            for value in prop.values:
                value = copy.deepcopy(value)
                prop_uploaded.append(value)

                val_uploaded = session.set(value)
                created_objects.append(val_uploaded)

        for child_section in section.sections:
            upload_section_recursive(child_section, sec_uploaded)

        return sec_uploaded

    # start recursive upload
    try:
        sec_uploaded = upload_section_recursive(section, None)
        return session.get(sec_uploaded.location, recursive=True, refresh=True)
    except RuntimeError as e:
        delete_all(session, created_objects)
        raise e


def upload_neo_structure(session, neo_object):
    """
    Upload a whole neo structure recursively.

    :param session:
    :type session: Session
    :param neo_object:
    :type neo_object: object

    :return: The uploaded neo object
    :rtype: object
    """
    processed = {}

    # define simple closures that upload a specific neo object
    def upload_block(block):
        if block not in processed:
            block_uploaded = session.set(block)
            processed[block] = block_uploaded

            for segment in block.segments:
                upload_segment(segment, block_uploaded)

            for channel_group in block.recordingchannelgroups:
                upload_recording_channel_group(channel_group, block_uploaded)

            return block_uploaded

        else:
            return processed[block]

    def upload_segment(segment, block=None):
        if segment not in processed:
            seg_uploaded = session.set(segment)
            processed[segment] = seg_uploaded

            signals = (segment.analogsignals or []) + (segment.irregularlysampledsignals or [])
            for signal in signals:
                upload_signal(signal, seg_uploaded)

            for signal_array in segment.analogsignalarrays:
                upload_signal_array(signal_array, seg_uploaded)

            spikes = (segment.spikes or []) + (segment.spiketrains or [])
            for spike in spikes:
                upload_spike(spike, seg_uploaded)

            events_and_epochs = (segment.events or []) + (segment.eventarrays or [])
            events_and_epochs += (segment.epochs or []) + (segment.epocharrays or [])
            for obj in events_and_epochs:
                upload_event_or_epoch(obj, seg_uploaded)

        else:
            seg_uploaded = processed[segment]

        if block is not None:
            seg_uploaded.block = block
            seg_uploaded = session.set(seg_uploaded)
            processed[segment] = seg_uploaded

        return seg_uploaded

    def upload_recording_channel_group(channel_group, block=None):
        if channel_group not in processed:
            group_uploaded = session.set(channel_group)
            processed[channel_group] = group_uploaded

            for channel in channel_group.recordingchannels:
                upload_recording_channel(channel, group_uploaded)

            for unit in channel_group.units:
                upload_unit(unit, group_uploaded)

        else:
            group_uploaded = processed[channel_group]

        if block is not None:
            group_uploaded.block = block
            group_uploaded = session.set(group_uploaded)
            processed[channel_group] = group_uploaded

        return group_uploaded

    def upload_recording_channel(recording_channel, channel_group=None):
        if recording_channel not in processed:
            channel_uploaded = session.set(recording_channel)
            processed[recording_channel] = channel_uploaded

            signals = (recording_channel.analogsignals or []) + (recording_channel.irregularlysampledsignals or [])
            for signal in signals:
                upload_signal(signal, None, channel_uploaded)

        else:
            channel_uploaded = processed[recording_channel]

        if channel_group is not None:
            channel_uploaded.recordingchannelgroups.append(channel_group)
            channel_uploaded = session.set(channel_uploaded)
            processed[recording_channel] = channel_uploaded

        return channel_uploaded

    def upload_unit(unit, channel_group=None):
        if unit not in processed:
            unit_uploaded = session.set(unit)
            processed[unit] = unit_uploaded

            spikes = (unit.spikes or []) + (unit.spiketrains or [])
            for spike in spikes:
                upload_spike(spike, None, unit_uploaded)

        else:
            unit_uploaded = processed[unit]

        if channel_group is not None:
            unit_uploaded.recordingchannelgroup = channel_group
            unit_uploaded = session.set(unit_uploaded)
            processed[unit] = unit_uploaded

        return unit_uploaded

    def upload_spike(spike, segment=None, unit=None):
        if spike not in processed:
            spike_uploaded = session.set(spike)
            processed[spike] = spike_uploaded

        else:
            spike_uploaded = processed[spike]

        if segment is not None:
            spike_uploaded.segment = segment
            spike_uploaded = session.set(spike_uploaded)
            processed[spike] = spike_uploaded

        if unit is not None:
            spike_uploaded.unit = unit
            spike_uploaded = session.set(spike_uploaded)
            processed[spike] = spike_uploaded

        return spike_uploaded

    def upload_signal_array(signal_array, segment=None, channel_group=None):
        if signal_array not in processed:
            array_uploaded = session.set(signal_array)
            processed[signal_array] = array_uploaded

        else:
            array_uploaded = processed[signal_array]

        if segment is not None:
            array_uploaded.segment = segment
            array_uploaded = session.set(array_uploaded)
            processed[signal_array] = array_uploaded

        if channel_group is not None:
            array_uploaded.recordingchannelgroup = channel_group
            array_uploaded = session.set(array_uploaded)
            processed[signal_array] = array_uploaded

        return array_uploaded

    def upload_signal(signal, segment=None, channel=None):
        if signal not in processed:
            signal_uploaded = session.set(signal)
            processed[signal] = signal_uploaded

        else:
            signal_uploaded = processed[signal]

        if segment is not None:
            signal_uploaded.segment = segment
            signal_uploaded = session.set(signal_uploaded)
            processed[signal] = signal_uploaded

        if channel is not None:
            signal_uploaded.recordingchannel = channel
            signal_uploaded = session.set(signal_uploaded)
            processed[signal] = signal_uploaded

        return signal_uploaded

    def upload_event_or_epoch(obj, segment=None):
        if obj not in processed:
            uploaded = session.set(obj)
            processed[obj] = uploaded

        else:
            uploaded = processed[obj]

        if segment is not None:
            uploaded.segment = segment
            uploaded = session.set(uploaded)
            processed[obj] = uploaded

        return uploaded

    # select a matching upload function and start upload
    try:
        if isinstance(neo_object, neo.Block):
            uploaded = upload_block(neo_object)
        elif isinstance(neo_object, neo.Segment):
            uploaded = upload_segment(neo_object)
        elif isinstance(neo_object, neo.EventArray):
            uploaded = upload_event_or_epoch(neo_object)
        elif isinstance(neo_object, neo.Event):
            uploaded = upload_event_or_epoch(neo_object)
        elif isinstance(neo_object, neo.EpochArray):
            uploaded = upload_event_or_epoch(neo_object)
        elif isinstance(neo_object, neo.Epoch):
            uploaded = upload_event_or_epoch(neo_object)
        elif isinstance(neo_object, neo.RecordingChannelGroup):
            uploaded = upload_recording_channel_group(neo_object)
        elif isinstance(neo_object, neo.RecordingChannel):
            uploaded = upload_recording_channel(neo_object)
        elif isinstance(neo_object, neo.Unit):
            uploaded = upload_unit(neo_object)
        elif isinstance(neo_object, neo.SpikeTrain):
            uploaded = upload_spike(neo_object)
        elif isinstance(neo_object, neo.Spike):
            uploaded = upload_spike(neo_object)
        elif isinstance(neo_object, neo.AnalogSignalArray):
            uploaded = upload_signal_array(neo_object)
        elif isinstance(neo_object, neo.AnalogSignal):
            uploaded = upload_signal(neo_object)
        elif isinstance(neo_object, neo.IrregularlySampledSignal):
            uploaded = upload_signal(neo_object)
        else:
            raise RuntimeError("Not compatible type: " + str(type(neo_object)))

        return session.get(uploaded.location, recursive=True, refresh=True)
    except RuntimeError as e:
        if len(processed) > 0:
            delete_all(session, processed.keys())
        raise e
