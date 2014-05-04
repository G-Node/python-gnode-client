"""
Assuming I'm a neuroscientist, having recorded data already, and I want to use 
G-Node platform and benefit from it. Here is an example use case provided.
"""

import datetime
import odml, neo
import numpy as np
import quantities as pq


class UseCase(object):

    @staticmethod
    def _create_property(where, *args, **kwargs):
        kwargs.update('section', where)
        p = odml.Property(*args, **kwargs)
        where.append(p)
        
    @classmethod
    def populate_session_metadata(cls):
        """ creates common odML metadata for a recording session according to
        the metadata<date>.txt """

        create = cls._create_property

        # experiment
        session = odml.Section(type="RecordingSession", name="RecordingSession")

        create(
            session, 'ProjectName', "Local Field Potential and Spike Data in "
                                    "Saccade and Fixation Tasks", 
        )
        create(
            session, 'Author', ['Markus Wittenberg', 'Thomas Wachtler']
        )
        create(
            session, 'Location', 'Neurophysics, Philipps-Universitaet Marburg'
        )
        create(
            session, 'CorrespondingAuthor',
            'Thomas Wachtler; Dept. Biology II, LMU Munich; wachtler@bio.lmu.de'
        )
        create(session, 'RecordingDate', datetime.date(2008, 7, 7))

        # subject
        subject = odml.Section(name='Subject', type='Subject')

        create(subject, 'Species', 'Macaca mulatta')
        create(subject, 'Age', 6)
        create(subject, 'Name', 'Maoli')

        # preparation
        preparation = odml.Section(name='Preparation', type='Preparation')
        create(preparation, 'BehavioralStatus', 'Awake behaving')
        create(preparation, 'BrainRegion', 'V1')

        # hardware
        hardware = odml.Section(name='Hardware', type='Hardware')
        create(preparation, 'NumberOfElectrodes', '16')
        create(preparation, 'ElectrodeArrayGeometry', '4x4')
        create(preparation, 'ElectrodeSpacing', '750 x 750', unit='um')
        create(preparation, 'LfpDataAcquisition', 'CED 1401')
        create(preparation, 'LfpBandpassLowCutoff', '1', unit='Hz')
        create(preparation, 'LfpBandpassHighCutoff', '120', unit='Hz')
        create(preparation, 'LfpSamplingRate', '500', unit='Hz')
        create(preparation, 'BroadbandDataAcquisition', 'MultiChannelSystems')
        create(preparation, 'BroadbandSamplingRate', '25', unit='kHz')

        # stimulus container
        stimulus = odml.Section(name='Stimulus', type='Stimulus')

        # add all to experiment
        for sec in [subject, preparation, hardware, stimulus]:
            session.append(sec)

        return session

    @classmethod
    def populate_stimulus_metadata(cls, num, size, cond, color, orientation):

        create = cls._create_property

        stimulus = odml.Section(name='Trial %d' % num, type='Stimulus')
        create(stimulus, 'BackgroundLuminance', '25', unit='cd/m2')
        create(stimulus, 'StimulusType', 'SquareGrating')
        create(stimulus, 'NumberOfStimulusConditions', '120', unit='Hz')
        create(stimulus, 'StimulusSize', size, unit='deg')
        create(stimulus, 'Orientations', orientation, unit='deg')
        create(stimulus, 'Colors', color)
        create(stimulus, 'BehavioralConditions', cond)

        return stimulus

    @classmethod
    def populate_data(cls, name, paths, lfp_channels, sua_channels, limit=None):
        """
        reads data from LFP/SUA .dat files and builds Neo structure from it

        :param paths    {
                            'lfp_data': "/foo/bar/lfp080807data.dat",
                            'lfp_meta': "/foo/bar/lfp080807cond.dat",
                            'sua_data': "/foo/bar/sua080807data.dat",
                            'sua_data': "/foo/bar/sua080807cond.dat"
                        }
        """

        def convert_to_timeseries(line):
            """ Converts a string of floats into a list. """
            s = line.split(" ")
            for i in range(s.count('')):
                s.remove('')
            return [float(el) for el in s]

        def convert_to_spikeindexes(line):
            line = line.replace(' ', '')
            return [(-300.0 + 2.0*i) for i, e in enumerate(line) if e == '1']

        conditions = ["Fixation", "Saccade"]
        colors = ["0 deg (red)", "90 deg (blue)", "180 deg (green)", "270 deg (yellow)"]
        orientations = ["0 deg", "45 deg", "90 deg", "135 deg"]

        block = neo.Block(name="080707.dat")
        rcg = neo.RecordingChannelGroup(name="Electrodes")
        block.recordingchannelgroups.append(rcg)
        rcg.block = block

        # channels
        for ch, electrode in enumerate(lfp_channels):
            obj = neo.RecordingChannel(
                name='Electrode %d' % electrode, index=ch
            )
            obj.recordingchannelgroups.append(rcg)
            rcg.recordingchannels.append(obj)

        # single units
        for sua, electrode in enumerate(sua_channels):
            obj = neo.Unit(name='Single Unit (electrode %d)' % electrode)
            obj.recordingchannelgroup = rcg
            rcg.units.append(obj)

        # segments (trials)
        with open(paths['lfp_meta'], 'r') as f:
            for i, l in enumerate(f):
                if not i % len(lfp_channels) == 0:
                    continue

                trial, condition, color, orientation, channel = l.split(' ')
                section = cls.populate_stimulus_metadata(
                    trial, 1.3, conditions[int(condition)], colors[int(color)],
                    orientations[int(orientation)]
                )
                segment = neo.Segment(
                    name='Trial %d (%s, %s, %s)' % (
                        trial, conditions[int(condition)], colors[int(color)],
                        orientations[int(orientation)])
                )
                segment.metadata = section
                segment.block = block
                block.segments.append(segment)

        # analog signals (LFP data)
        metadata = open(paths['lfp_cond'],'r').readlines()
        dataset = open(paths['lfp_data'],'r').readlines()

        for meta, data in zip(metadata, dataset):

            trial, condition, color, orientation, channel = meta.split(' ')

            segment = block.segments[int(trial) - 1]
            rc = rcg.recordingchannels[int(channel) - 1]
            params = {
                'name': "LFP Signal (ch %s)" % (channel),
                't_start': -300.0 * pq.ms,
                'sampling_rate': 500 * pq.Hz,
                'signal': np.array(convert_to_timeseries(data)) * pq.mV,
            }
            obj = neo.AnalogSignal(**params)
            obj.segment = segment
            obj.recordingchannel = rc
            segment.analogsignals.append(obj)
            rc.analogsignals.append(obj)

        # spike trains (SUA data)
        metadata = open(paths['sua_cond'],'r').readlines()
        dataset = open(paths['sua_data'],'r').readlines()

        for meta, data in zip(metadata, dataset):

            trial, condition, color, orientation, unit = meta.split(' ')

            segment = block.segments[int(trial) - 1]
            unit = rcg.units[int(unit) - 1]
            params = {
                'name': "SpikeTrain (SUA %s)" % (unit + 1),
                't_start': -300.0 * pq.ms,
                't_stop': 698.0 * pq.ms,
                'times': np.array(convert_to_spikeindexes(data)) * pq.ms,
            }
            obj = neo.SpikeTrain(**params)
            obj.segment = segment
            obj.unit = unit
            segment.spiketrains.append(obj)
            unit.spiketrains.append(obj)

        return block


if 0: # not implemented yet

    # STEP 1 - 2
    """ First, the spike times should be scaled because sampling rate 
    was 500Hz, i.e., the values have to be multiplied by 2 to represent time in 
    ms. Furthermore, trials are time-aligned to stimulus onset or saccade end, 
    respectively, which should be t=0. This means that 300ms should be 
    subtracted from spike times, and the first value of the lfp traces 
    corresponds to t=-300 ms."""

    # option 1
    for segment in b.segments():
        for st in segment.spiketrains:
            st.times *= 2.0
            st.times -= 300.0
            st.save() # sends data to the server

    # option 2
    for st in gnode.select("spiketrain", segment__in = b.segments()):
        st.times *= 2.0
        st.times -= 300.0
        st.save() # sends data to the server


    # STEP 3
    """ For each LFP channel, calculate the averages of the LFP traces over all 
    trials for each unique experimental condition (2 behav cond, 4x4 stimuli). 
    Save the averages because they will be used often. Plot the LFP responses 
    together with the mean for a given LFP channel, color, and orientation."""

    averages = b.add_segment("Averages") # a fake segment to store averages
    for cond in p_cond.values():
        for color in p_color.values():
            for angle in p_orient.values():
                for channel in b.recordingchannels:
                    """ notice here, we filter signals which do not have DIRECT 
                    experimental conditions assigned (color etc.) but the following
                    should still work through implicit filtering (through segment 
                    relation, which holds these attributes)."""

                    # data from relevant block, channel, condition, color and angle
                    # option 1
                    signals = gnode.select("analogsignal", block = b) # query should not be evaluated here!!
                    signals = signals.filter(recordingchannel=channel) # neither here!!
                    # nor here!!
                    signals = signals.filter(metadata = (p_cond, cond))
                    signals = signals.filter(metadata = (p_color, color))
                    signals = signals.filter(metadata = (p_orient, angle))

                    # OR option 2
                    criteria = {
                        "block": b,
                        "recordingchannel": channel,
                        "metadata1": (p_cond, cond),
                        "metadata2": (p_color, color),
                        "metadata3": (p_orient, angle)
                    }
                    signals = gnode.select("analogsignal", **criteria)

                    # query should be evaluated only at next line
                    averaged_signal = signals[0].clone() # this is interesting, ah?
                    averaged_signal.signal = to_array(signals).mean(axis=0) # ?!
                     # should it be already numpy arrays?
                    averaged_signal.segment = averages
                    averaged_signal.save()

    # STEP 4
    """ Plot the LFP responses together with the mean for a given LFP channel, 
    color, and orientation. Here let's take condition = FIX, color = red, 
    orientation = 45 grad, channel = 5."""

    import matplotlib.pyplot as plt
    criteria = {
        "recordingchannel": gnode.select("recordingchannel", block=b, index=5),
        "metadata1": (p_cond, "fixation"),
        "metadata2": (p_color, "red"),
        "metadata3": (p_orient, "45")
    }
    selected = gnode.select("analogsignal", **criteria)

    # within selected should be all signals, including the average
    plt.plot(selected)

    # STEP 5
    """ Determine the peak values of the average LFP responses and find the LFP
    channel with the largest difference between largest and smallest peak values
    across stimuli."""

    deltas = []
    for channel in b.recordingchannels:
        selected = gnode.select("analogsignal", segment = averages, recordingchannel = channel)
        ar = to_array(selected) # should it be already numpy arrays?
        delta = abs(ar.max() - ar.min())
        if delta > max(deltas): res_ch = channel # the winning channel
        deltas.append(delta)

    # STEP 6
    """ Make a dataset that contains all available data (lfp and spikes) from
    the corresponding electrode and share it with user XY."""

    """ this should automatically share all related objects, like analogsignals,
    spiketrains, units, block etc. """
    res_ch.share_with(name="XY")

    # STEP 7 - 8
    """ For each SUA channel, calculate the mean spike rate in the 100ms time 
    interval starting 40ms after stimulus onset/saccade end for each stimulus in
    a given behavioral condition. The resulting two sets of 16 response values 
    (4x4 response matrices) represent the stimulus selectivities that 
    characterize the unit. Save the values because they will be used often."""

    rs.add_section("Analysis", template="analysis") # switch the logging on?

    # TODO

    #---------------------------------------------------------------------------

    """ Opened questions:
    - how do blocks (segments etc.) relate to their metadata?!
    - what to do with duplicates?
    - where to assign experimental conditions - to segment or to analogsignal? or both?


        Important functions:
    - <object_type>.filter(conditions, names etc.) or <queryset>.filter
    - making an ndim array from queryset..

    """

    #---------------------------------------------------------------------------

