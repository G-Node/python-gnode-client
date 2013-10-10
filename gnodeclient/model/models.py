from __future__ import print_function, absolute_import, division

from gnodeclient.util.declarative_models import Field
from gnodeclient.model.model_base import RestResult, Models
from gnodeclient.model.model_fields import FQuantity, FDatafile, FParent, FChildren


class SectionModel(RestResult):
    model       = Field(field_type=str, default=Models.SECTION)
    name        = Field(field_type=str, obligatory=True)
    description = Field(field_type=str)

    parent      = FParent(type_info=Models.SECTION)
    properties  = FChildren(type_info=Models.PROPERTY)

Models._MODEL_MAP[Models.SECTION] = SectionModel


class PropertyModel(RestResult):
    model       = Field(field_type=str, default=Models.PROPERTY)
    name        = Field(field_type=str, obligatory=True)

    parent      = FParent(type_info=Models.SECTION)
    values      = FChildren(type_info=Models.VALUE, obligatory=True)

Models._MODEL_MAP[Models.PROPERTY] = PropertyModel


class ValueModel(RestResult):
    model       = Field(field_type=str, default=Models.VALUE)
    value       = Field(field_type=str, obligatory=True)

    parent      = FParent(type_info=Models.PROPERTY)

Models._MODEL_MAP[Models.VALUE] = ValueModel


class BlockModel(RestResult):
    model       = Field(field_type=str, default=Models.BLOCK)
    name        = Field(field_type=str)
    index       = Field(field_type=int, default=0)
    description = Field(field_type=str)

    recordingchannelgroups = FChildren(type_info=Models.RECORDINGCHANNELGROUP)
    segments               = FChildren(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.BLOCK] = BlockModel


class SegmentModel(RestResult):
    model       = Field(field_type=str, default=Models.SEGMENT)
    name        = Field(field_type=str)
    index       = Field(default=0)

    block       = FParent(type_info=Models.BLOCK)

    analogsignals             = FChildren(type_info=Models.ANALOGSIGNAL)
    irregularlysampledsignals = FChildren(type_info=Models.IRREGULARLYSAMPLEDSIGNAL)
    analogsignalarrays        = FChildren(type_info=Models.ANALOGSIGNALARRAY)
    spiketrains               = FChildren(type_info=Models.SPIKETRAIN)
    spikes                    = FChildren(type_info=Models.SPIKE)
    events                    = FChildren(type_info=Models.EVENT)
    epochs                    = FChildren(type_info=Models.EPOCH)

Models._MODEL_MAP[Models.SEGMENT] = SegmentModel


class EventArrayModel(RestResult):
    model       = Field(field_type=str, default=Models.EVENTARRAY)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    times       = FDatafile(obligatory=True)

    segment     = FParent(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EVENTARRAY] = EventArrayModel


class EventModel(RestResult):
    model       = Field(field_type=str, default=Models.EVENT)
    name        = Field(field_type=str)
    description = Field(field_type=str)
    label       = Field(obligatory=True, field_type=str, default="")

    time        = FQuantity(obligatory=True)

    segment     = FParent(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EVENT] = EventModel


class EpochArrayModel(RestResult):
    model       = Field(field_type=str, default=Models.EPOCHARRAY)
    name        = Field(field_type=str)
    description = Field(field_type=str)
    labels      = Field(obligatory=True, field_type=list)

    times       = FDatafile(obligatory=True)
    durations   = FDatafile(obligatory=True)

    segment     = Field(is_parent=True, type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EPOCHARRAY] = EpochArrayModel


class EpochModel(RestResult):
    model       = Field(field_type=str, default=Models.EPOCH)
    name        = Field(field_type=str)
    description = Field(field_type=str)
    label       = Field(obligatory=True, field_type=str, default="")

    time        = FQuantity(obligatory=True)
    duration    = FQuantity(obligatory=True)

    segment     = FParent(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.EPOCH] = EpochModel


class RecordingChannelGroupModel(RestResult):
    model       = Field(field_type=str, default=Models.RECORDINGCHANNELGROUP)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    block       = FParent(type_info=Models.BLOCK)
    units       = FChildren(type_info=Models.UNIT)
    recordingchannels   = FChildren(type_info=Models.RECORDINGCHANNEL)
    analogsignalarrays  = FChildren(type_info=Models.ANALOGSIGNALARRAY)

Models._MODEL_MAP[Models.RECORDINGCHANNELGROUP] = RecordingChannelGroupModel


class RecordingChannelModel(RestResult):
    model       = Field(field_type=str, default=Models.RECORDINGCHANNEL)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    recordingchannelgroups    = FChildren(type_info=Models.RECORDINGCHANNELGROUP)
    analogsignals             = FChildren(type_info=Models.ANALOGSIGNAL)
    irregularlysampledsignals = FChildren(type_info=Models.IRREGULARLYSAMPLEDSIGNAL)

Models._MODEL_MAP[Models.RECORDINGCHANNEL] = RecordingChannelModel


class UnitModel(RestResult):
    model       = Field(field_type=str, default=Models.UNIT)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    recordingchannelgroup   = FParent(type_info=Models.RECORDINGCHANNELGROUP)
    spikes                  = FChildren(type_info=Models.SPIKE)
    spiketrains             = FChildren(type_info=Models.SPIKETRAIN)

Models._MODEL_MAP[Models.UNIT] = UnitModel


class SpikeTrainModel(RestResult):
    model       = Field(field_type=str, default=Models.SPIKETRAIN)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    t_start     = FQuantity()
    t_stop      = FQuantity(obligatory=True)
    times       = FDatafile(obligatory=True)
    waveforms   = FDatafile()

    unit        = FParent(type_info=Models.UNIT)
    segment     = FParent(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.SPIKETRAIN] = SpikeTrainModel


class SpikeModel(RestResult):
    model       = Field(field_type=str, default=Models.SPIKE)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    time            = FQuantity(obligatory=True)
    left_sweep      = FQuantity()
    sampling_rate   = FQuantity()
    waveform        = FDatafile()

    unit        = FParent(type_info=Models.UNIT)
    segment     = FParent(type_info=Models.SEGMENT)

Models._MODEL_MAP[Models.SPIKE] = SpikeModel


class AnalogsignalArrayModel(RestResult):
    model       = Field(field_type=str, default=Models.ANALOGSIGNALARRAY)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    t_start         = FQuantity()
    sampling_rate   = FQuantity(obligatory=True)
    signal          = FDatafile(obligatory=True)

    segment                 = FParent(type_info=Models.SEGMENT)
    recordingchannelgroup   = FParent(type_info=Models.RECORDINGCHANNELGROUP)

Models._MODEL_MAP[Models.ANALOGSIGNALARRAY] = AnalogsignalArrayModel


class AnalogsignalModel(RestResult):
    model       = Field(field_type=str, default=Models.ANALOGSIGNAL)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    t_start         = FQuantity()
    sampling_rate   = FQuantity(obligatory=True)
    signal          = FDatafile(obligatory=True)

    segment          = FParent(type_info=Models.SEGMENT)
    recordingchannel = FParent(type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.ANALOGSIGNAL] = AnalogsignalModel


class IrregularlySampledSignalModel(RestResult):
    model       = Field(field_type=str, default=Models.IRREGULARLYSAMPLEDSIGNAL)
    name        = Field(field_type=str)
    description = Field(field_type=str)

    #t_start    = FQuantity()
    signal      = FDatafile(obligatory=True)
    times       = FDatafile(obligatory=True)

    segment          = FParent(type_info=Models.SEGMENT)
    recordingchannel = FParent(type_info=Models.RECORDINGCHANNEL)

Models._MODEL_MAP[Models.IRREGULARLYSAMPLEDSIGNAL] = IrregularlySampledSignalModel
