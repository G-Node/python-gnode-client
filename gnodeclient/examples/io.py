
import odml, neo
import numpy as np
import quantities as pq
from gnodeclient.tools import upload_neo_structure, upload_odml_tree


class UseCase(object):

    @staticmethod
    def _create_property(where, *args, **kwargs):
        kwargs.update('section', where)
        p = odml.Property(*args, **kwargs)
        where.append(p)

    @classmethod
    def populate_session_metadata(cls, date):
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
        create(session, 'RecordingDate', date)

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
        """ creates a metadata section for a certain experimental trial

        :param num:             trial number
        :param size:            stimulus size
        :param cond:            behavioural condition
        :param color:           stimulus color
        :param orientation:     stimulus orientation
        :return:                created odML section
        """
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
    def populate_dataset(cls, name, lfp_channels, sua_channels):
        """
        reads data from LFP/SUA .dat files and builds Neo structure from it
        """
        block = neo.Block(name=name)
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

        return block

    @classmethod
    def read_lfp_data(cls, paths):
        """
        Generator that returns Analog Signals from a given file path

        :param paths    {
            'lfp_data': "/foo/bar/lfp080807data.dat",
            'lfp_cond': "/foo/bar/lfp080807cond.dat"
        }
        """

        def convert_to_timeseries(line):
            """ Converts a string of floats into a list. """
            s = line.split(" ")
            for i in range(s.count('')):
                s.remove('')
            return [float(el) for el in s]

        metadata = open(paths['lfp_cond'], 'r').readlines()
        dataset = open(paths['lfp_data'], 'r').readlines()

        for meta, data in zip(metadata, dataset):

            trial, condition, color, orientation, channel = meta.split(' ')

            params = {
                'name': "LFP Signal (ch %s)" % (channel),
                't_start': -300.0 * pq.ms,
                'sampling_rate': 500 * pq.Hz,
                'signal': np.array(convert_to_timeseries(data)) * pq.mV,
            }

            yield (int(trial), int(channel), neo.AnalogSignal(**params))

    @classmethod
    def read_sua_data(cls, paths):
        """
        Generator that returns Spike Trains from a given file path

        :param paths    {
            'sua_data': "/foo/bar/sua080807data.dat",
            'sua_cond': "/foo/bar/sua080807cond.dat"
        }
        """

        def convert_to_spikeindexes(line):
            line = line.replace(' ', '')
            return [(-300.0 + 2.0*i) for i, e in enumerate(line) if e == '1']

        metadata = open(paths['sua_cond'], 'r').readlines()
        dataset = open(paths['sua_data'], 'r').readlines()

        for meta, data in zip(metadata, dataset):

            trial, condition, color, orientation, unit = meta.split(' ')

            params = {
                'name': "SpikeTrain (SUA %s)" % (unit + 1),
                't_start': -300.0 * pq.ms,
                't_stop': 698.0 * pq.ms,
                'times': np.array(convert_to_spikeindexes(data)) * pq.ms,
            }

            yield (int(trial), int(unit), neo.SpikeTrain(**params))


    @classmethod
    def upload_session(cls, connection, doc, date, paths, lfp_channels,
                       sua_channels, conditions, colors, orientations):
        """
        Uploads complete experimental recording session.

        :param connection:      opened connection to the remote server
        :param doc:             odML document to connect metadata to
        :param date:            recording session date
        :param paths:           paths to data files like {
                                    'lfp_data': "/foo/bar/lfp080807data.dat",
                                    'lfp_cond': "/foo/bar/lfp080807cond.dat"
                                    'sua_data': "/foo/bar/sua080807data.dat",
                                    'sua_cond': "/foo/bar/sua080807cond.dat"
                                }
        :param lfp_channels:    list of electrode numbers
        :param sua_channels:    list of SUA numbers
        :param conditions:      list of behavioural conditions
        :param colors:          list of stimulus colors
        :param orientations:    list of stimulus orientations
        :return:
        """

        # create common metadata
        metadata = cls.populate_session_metadata(date)
        metadata._parent = doc
        metadata = upload_odml_tree(connection, metadata)

        # create trials (Neo Segments with odML Sections)
        block = cls.populate_dataset(
            "%s.dat" % date.strftime("%y%m%d"), lfp_channels, sua_channels
        )
        stimulus = filter(lambda x: x.type == 'Stimulus', metadata.sections)[0]
        with open(paths['lfp_meta'], 'r') as f:
            for i, l in enumerate(f):
                if not i % len(lfp_channels) == 0:  # len(lfp_channels)
                    continue

                trial, condition, color, orientation, channel = l.split(' ')
                section = cls.populate_stimulus_metadata(
                    trial, 1.3, conditions[int(condition)],
                    colors[int(color)], orientations[int(orientation)]
                )
                section._parent = stimulus
                stimulus.append(section)
                section = connection.set(section)

                segment = neo.Segment(
                    name='Trial %d (%s, %s, %s)' % (
                        trial, conditions[int(condition)], colors[int(color)],
                        orientations[int(orientation)])
                )
                segment.metadata = section
                segment.block = block
                block.segments.append(segment)

        # read LFP data
        for trial, channel, signal in cls.read_lfp_data(paths):
            segment = block.segments[trial - 1]
            rc = block.recordingchannelgroups[0].recordingchannels[channel - 1]
            signal.segment = segment
            signal.recordingchannel = rc
            segment.analogsignals.append(signal)
            rc.analogsignals.append(signal)

        # read SUA data
        for trial, unit, spiketrain in cls.read_sua_data(paths):
            segment = block.segments[trial - 1]
            unit = block.recordingchannelgroups[0].units[unit - 1]
            spiketrain.segment = segment
            spiketrain.unit = unit
            segment.spiketrains.append(spiketrain)
            unit.spiketrains.append(spiketrain)

        upload_neo_structure(connection, block)

        return metadata, block


