"""
Assuming I'm a neuroscientist, having recorded data already, and I want to use 
G-Node platform and benefit from it. Here is an example use case provided.
"""

import datetime
import odml, neo
import quantities as pq


class UseCase(object):

    @staticmethod
    def populate_metadata():
        """ creates odML metadata according to the metadata.txt """

        # experiment
        session = odml.Section(type="RecordingSession", name="RecordingSession")

        p1 = odml.Property(
            'ProjectName', "Local Field Potential and Spike Data in Saccade "
                           "and Fixation Tasks", session
        )
        p2 = odml.Property(
            'Author', ['Markus Wittenberg', 'Thomas Wachtler'], session
        )
        p3 = odml.Property(
            'Location', 'Neurophysics, Philipps-Universitaet Marburg', session
        )
        p4 = odml.Property(
            'CorrespondingAuthor',
            'Thomas Wachtler; Dept. Biology II, LMU Munich; wachtler@bio.lmu.de',
            session
        )
        p5 = odml.Property('RecordingDate', datetime.date(2008, 7, 7), session)

        for p in [p1, p2, p3, p4, p5]:
            session.append(p)

        # subject
        subject = odml.Section(name='Subject', type='Subject')

        p1 = odml.Property('Species', 'Macaca mulatta', subject)
        p2 = odml.Property('Age', 6, subject)
        p3 = odml.Property('Name', 'Maoli', subject)

        for p in [p1, p2, p3]:
            subject.append(p)

        # preparation
        preparation = odml.Section(name='Preparation', type='Preparation')
        p1 = odml.Property('BehavioralStatus', 'Awake behaving', preparation)
        p2 = odml.Property('BrainRegion', 'V1', preparation)

        for p in [p1, p2]:
            preparation.append(p)

        # hardware
        hardware = odml.Section(name='Hardware', type='Hardware')
        p1 = odml.Property('NumberOfElectrodes', '16', preparation)
        p2 = odml.Property('ElectrodeArrayGeometry', '4x4', preparation)
        p3 = odml.Property('ElectrodeSpacing', '750 x 750', preparation, unit='um')
        p4 = odml.Property('LfpDataAcquisition', 'CED 1401', preparation)
        p5 = odml.Property('LfpBandpassLowCutoff', '1', preparation, unit='Hz')
        p6 = odml.Property('LfpBandpassHighCutoff', '120', preparation, unit='Hz')
        p7 = odml.Property('LfpSamplingRate', '500', preparation, unit='Hz')
        p8 = odml.Property('BroadbandDataAcquisition', 'MultiChannelSystems', preparation)
        p9 = odml.Property('BroadbandSamplingRate', '25', preparation, unit='kHz')

        for p in [p1, p2, p3, p4, p5, p6, p7, p8, p9]:
            hardware.append(p)

        # stimulus
        stimulus = odml.Section(name='Stimulus', type='Stimulus')
        p1 = odml.Property('BackgroundLuminance', '25', stimulus, unit='cd/m2')
        p2 = odml.Property('StimulusType', 'SquareGrating', stimulus)
        p3 = odml.Property('StimulusSize', '1.3', stimulus, unit='deg')
        p4 = odml.Property('Orientations', ['0', '45', '90', '135'], stimulus, unit='deg')
        p5 = odml.Property('Colors', ['red', 'green', 'blue', 'yellow'], stimulus)
        p6 = odml.Property('NumberOfStimulusConditions', '120', stimulus, unit='Hz')
        p7 = odml.Property('BehavioralConditions', ['Fixation', 'Saccade'], stimulus)

        for p in [p1, p2, p3, p4, p5, p6, p7]:
            stimulus.append(p)

        # format
        fmt = odml.Section(name='Format', type='Format')

        p1 = odml.Property(
            'DataFileStructure',
            ["TrialDataPoints", "TrialOfGivenCondition", "Colors", "Orientations",
             "Channels"],
            fmt
        )
        p2 = odml.Property('TotalNumberOfLfpFixationTrials', [500, 11, 4, 4, 12], fmt)
        p3 = odml.Property('TotalNumberOfLfpSaccadeTrials', [500, 23, 4, 4, 12], fmt)
        p4 = odml.Property('TotalNumberOfSuaFixationTrials', [500, 11, 4, 4,  5], fmt)
        p5 = odml.Property('TotalNumberOfSuaSaccadeTrials', [500, 23, 4, 4,  5], fmt)

        for p in [p1, p2, p3, p4, p5]:
            fmt.append(p)

        # add all to experiment
        for sec in [subject, preparation, hardware, stimulus, fmt]:
            session.append(sec)

        return session

    @staticmethod
    def populate_data(path):
        """
        reads data from LFP/SUA .dat files and builds Neo structure from it
        """

        def convert_to_timeseries(line):
            """ Converts a string of tab(?) separated floats into a list. """
            s = line.split('  ')
            while '' in s:
                s.remove('')
            return [float(x) for x in s]

        # 1. create a dataset
        b = neo.core.Block() # LFPs only
        b.name = "Macaque Monkey Recordings, LFPs, V1"
        b.section = experiment

        # 2. create channels
        indexes = [1, 2, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16]
        rcg = neo.core.RecordingChannelGroup(name='RCG', channel_indexes=indexes)
        b.recordingchannelgroups.append(rcg)
        rcg.block = b

        for index in rcg.channel_indexes:
            r = neo.core.RecordingChannel()
            r.name = 'Channel %d' % index
            r.index = index
            r.recordingchannelgroups.append(rcg)
            rcg.recordingchannels.append(r)


        # 3. create trial segments and signal data
        with open('/home/andrey/data/080707/lfp_fix080707.dat', 'r') as f:

            for i, l in enumerate(f):

                if i < 176: # create segment every line for first 176 lines
                    s = neo.core.Segment(name = str(i)) # create new segment
                    s.block = b
                    b.segments.append(s)

                else:
                    s = b.segments[ i % 176 ]

                if (i % 176) == 0: # get new channel every 176 lines
                    r = rcg.recordingchannels[ i / 176 ]

                # creating analogsignal
                data = convert_to_timeseries(l) * pq.mV

                kwargs = {}
                kwargs['name'] = 'Trial %d Ch %d' % (i % 176, i / 176)
                kwargs['t_start'] = 0 * pq.ms

                sr = 500.0 #float(hardware.properties['LfpSamplingRate'].value.data)
                sr_units = 'Hz' #hardware.properties['LfpSamplingRate'].value.unit
                kwargs['sampling_rate'] = sr * getattr(pq, sr_units)

                signal = neo.core.AnalogSignal(data, **kwargs)

                signal.segment = s
                s.analogsignals.append(signal)

                signal.recordingchannel = r
                r.analogsignals.append(signal)

        # TODO import LFP SAC

        # TODO import SUA FIX

        # TODO import SUA SAC

        return b



# select synced experiment
#experiments = g.select('section', {'parent_section__isnull': 1})
#experiments.sort(key=lambda x: x.location, reverse=True)
#experiment = experiments[0]

#sections = g.select('section', {'parent_section__id': experiment._gnode['id'], 'name': 'Stimulus'})
#stimulus = g.pull(sections[0]._gnode['location'])

#blocks = g.select('block')
#blocks.sort(key=lambda x: x._gnode['id'], reverse=True)
#b = g.pull(blocks[0]._gnode['location'])



if 0: # not implemented yet

    # 3. annotate
    #-------------------------------------------------------------------------------

    for i, s in enumerate(b.segments):
        color_index = (i / 48) % 4
        orient_index = (i / 12) % 4
        cond_index = 0

        color = stimulus.properties['Colors'].values[ color_index ]
        orient = stimulus.properties['Orientations'].values[ orient_index ]
        cond = stimulus.properties['BehavioralConditions'].values[ cond_index ]

        g.annotate([s], [color, orient, cond])


        # 4. use case
        #-------------------------------------------------------------------------------

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

