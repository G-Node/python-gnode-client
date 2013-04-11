"""
Assuming I'm a neuroscientist, having recorded data already, and I want to use 
G-Node platform and benefit from it. Here is an example use case provided.
"""

import datetime
from session import init

def convert_to_timeseries(line):
    """ Converts a string of tab(?) separated floats into a list. """
    s = line.split('  ')

    while '' in s:
        s.remove('')

    return [float(x) for x in s]


g = init() # start a session

metadata_created = False
data_created = False
annotated = False

if not metadata_created:
    # 1. create METADATA
    #-------------------------------------------------------------------------------

    g.terminologies # displays available metadata terminologies
    """
    Out[16]: 
    [<Section Analysis[analysis] (0)>,
     <Section PSTH[analysis/psth] (0)>,
     <Section PowerSpectrum[analysis/power_spectrum] (0)>,
     <Section Cell[cell] (0)>,
     ...
    """

    # 1. describe experiment
    experiment = g.terminologies['Experiment'].clone() # Experiment root section
    experiment.name = 'Local Field Potential and Spike Data in Saccade and Fixation Tasks'

    experiment.properties # shows the default generated properties
    """
    Out[11]: 
    [<Property Description>,
     <Property Type>,
     <Property Subtype>,
     <Property ProjectName>,
     <Property ProjectID>]
    """


    experiment.properties['ProjectName'].value.data = 'Local Field Potential and Spike Data in Saccade and Fixation Tasks'

    # need to create some custom properties
    from odml.property import BaseProperty as Property
    p1 = Property('Author', ['Markus Wittenberg', 'Thomas Wachtler'], experiment)
    p2 = Property('Location', 'Neurophysics, Philipps-Universitaet Marburg', experiment)
    p3 = Property('CorrespondingAuthor', 'Thomas Wachtler; Dept. Biology II, LMU Munich; wachtler@bio.lmu.de', experiment)
    p4 = Property('RecordingDate', datetime.date(2008, 7, 7), experiment)

    # FIXME odml works one way only so these has to be added to the experiment
    for p in [p1, p2, p3, p4]:
        experiment.append( p )


    # 2. describe subject
    subject = g.terminologies['Subject'].clone()

    subject.properties['Species'].value = 'Macaca mulatta'
    subject.properties['Age'].value = 6

    p = Property('Name', 'Maoli', subject)
    subject.append( p )


    # 3. preparation
    preparation = g.terminologies['Preparation'].clone()
    p1 = Property('BehavioralStatus', 'Awake behaving', preparation)
    p2 = Property('BrainRegion', 'V1', preparation)

    for p in [p1, p2]:
        preparation.append( p )


    # 4. hardware
    hardware = g.terminologies['Hardware'].clone()
    p1 = Property('NumberOfElectrodes', '16', preparation)
    p2 = Property('ElectrodeArrayGeometry', '4x4', preparation)
    p3 = Property('ElectrodeSpacing', '750 x 750', preparation, unit='um')
    p4 = Property('LfpDataAcquisition', 'CED 1401', preparation)
    p5 = Property('LfpBandpassLowCutoff', '1', preparation, unit='Hz')
    p6 = Property('LfpBandpassHighCutoff', '120', preparation, unit='Hz')
    p7 = Property('LfpSamplingRate', '500', preparation, unit='Hz')
    p8 = Property('BroadbandDataAcquisition', 'MultiChannelSystems', preparation)
    p9 = Property('BroadbandSamplingRate', '25', preparation, unit='kHz')

    for p in [p1, p2, p3, p4, p5, p6, p7, p8, p9]:
        hardware.append( p )


    # 5. stimulus
    stimulus = g.terminologies['Stimulus'].clone()
    p1 = Property('BackgroundLuminance', '25', stimulus, unit='cd/m2')
    p2 = Property('StimulusType', 'SquareGrating', stimulus)
    p3 = Property('StimulusSize', '1.3', stimulus, unit='deg')
    p4 = Property('Orientations', ['0', '45', '90', '135'], stimulus, unit='deg')
    p5 = Property('Colors', ['red', 'green', 'blue', 'yellow'], stimulus)
    p6 = Property('NumberOfStimulusConditions', '120', stimulus, unit='Hz')
    p7 = Property('BehavioralConditions', ['Fixation', 'Saccade'], stimulus)

    for p in [p1, p2, p3, p4, p5, p6, p7]:
        stimulus.append( p )


    # 6. format
    from odml.section import BaseSection as Section
    format = Section('Format', 'Format', experiment)

    p1 = Property('DataFileStructure', ["TrialDataPoints", "TrialOfGivenCondition",\
            "Colors", "Orientations", "Channels"], format)
    p2 = Property('TotalNumberOfLfpFixationTrials', [500, 11, 4, 4, 12], format)
    p3 = Property('TotalNumberOfLfpSaccadeTrials', [500, 23, 4, 4, 12], format)
    p4 = Property('TotalNumberOfSuaFixationTrials', [500, 11, 4, 4,  5], format)
    p5 = Property('TotalNumberOfSuaSaccadeTrials', [500, 23, 4, 4,  5], format)

    for p in [p1, p2, p3, p4, p5]:
        format.append( p )


    # add all to experiment
    for sec in [subject, preparation, hardware, stimulus, format]:
        experiment.append( sec )

    g.sync( experiment, cascade=True ) # sync all

else:
    experiments = g.list('section', {'parent_section__isnull': 1})
    experiments.sort(key=lambda x: x._gnode['id'], reverse=True)
    experiment = experiments[0]

    sections = g.list('section', {'parent_section__id': experiment._gnode['id'], 'name': 'Stimulus'})
    stimulus = g.pull( sections[0]._gnode['location'] )


# 2. create DATA
#-------------------------------------------------------------------------------
import quantities as pq
import neo

if not data_created:
    # 1. create a dataset
    b = neo.core.Block() # LFPs only
    b.name = "Macaque Monkey Recordings, LFPs, V1"
    b.section = experiment

    # 2. create channels
    indexes = [1, 2, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16]
    rcg = neo.core.RecordingChannelGroup( name='RCG', channel_indexes=indexes )
    b.recordingchannelgroups.append( rcg )
    rcg.block = b

    for index in rcg.channel_indexes:
        r = neo.core.RecordingChannel()
        r.name = 'Channel %d' % index
        r.index = index
        r.recordingchannelgroups.append( rcg )
        rcg.recordingchannels.append( r )


    # 3. create trial segments and signal data
    with open('/home/sobolev/data/080707/lfp_fix080707.dat', 'r') as f:

        for i, l in enumerate(f):

            if i < 176: # create segment every line for first 176 lines
                s = neo.core.Segment(name = str(i)) # create new segment
                s.block = b
                b.segments.append( s )

            else:
                s = b.segments[ i % 176 ]

            if (i % 176) == 0: # get new channel every 176 lines
                r = rcg.recordingchannels[ i / 176 ]

            # creating analogsignal
            data = convert_to_timeseries( l ) * pq.mV

            kwargs = {}
            kwargs['t_start'] = 0 * pq.ms

            sr = 500.0 #float( hardware.properties['LfpSamplingRate'].value.data )
            sr_units = 'Hz' #hardware.properties['LfpSamplingRate'].value.unit
            kwargs['sampling_rate'] = sr * getattr(pq, sr_units)

            signal = neo.core.AnalogSignal(data, **kwargs)

            signal.segment = s
            s.analogsignals.append( signal )

            signal.recordingchannel = r
            r.analogsignals.append( signal )

    # TODO import LFP SAC

    # TODO import SUA FIX

    # TODO import SUA SAC

    g.sync( b, cascade=True )

else:
    blocks = g.list('block')
    blocks.sort(key=lambda x: x._gnode['id'], reverse=True)
    b = g.pull(blocks[0]._gnode['location'])

# 3. annotate
#-------------------------------------------------------------------------------

for i, s in enumerate( b.segments ):
    color_index = (i / 48) % 4
    orient_index = (i / 12) % 4
    cond_index = 0

    color = stimulus.properties['Colors'].values[ color_index ]
    orient = stimulus.properties['Orientations'].values[ orient_index ]
    cond = stimulus.properties['BehavioralConditions'].values[ cond_index ]

    g.annotate([s], [color, orient, cond])


