
import odml
import neo
import quantities as pq
from gnodeclient.tools import sync_obj_tree


class UseCase(object):

    @staticmethod
    def _create_property(where, name, value, **kwargs):
        prop = odml.Property(name, odml.Value(value, **kwargs))
        where.append(prop)

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

        stimulus = odml.Section(name='Trial %s' % num, type='Stimulus')
        create(stimulus, 'BackgroundLuminance', '25', unit='cd/m2')
        create(stimulus, 'StimulusType', 'SquareGrating')
        create(stimulus, 'NumberOfStimulusConditions', '120', unit='Hz')
        create(stimulus, 'StimulusSize', size, unit='deg')
        create(stimulus, 'Orientation', orientation, unit='deg')
        create(stimulus, 'Color', color)
        create(stimulus, 'BehavioralCondition', cond)

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
                'signal': pq.Quantity(convert_to_timeseries(data), units="uV"),
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

        def convert_to_spikelist(spike_times):
            if len(spike_times) > 0:
                return [int(x) for x in spike_times]
            return [0]

        metadata = open(paths['sua_cond'], 'r').readlines()
        dataset = open(paths['sua_data'], 'r').readlines()

        for meta, data in zip(metadata, dataset):

            trial, condition, color, orientation, unit = meta.split(' ')
            data_split = data.split(" ")
            spike_times = data_split[1:]

            if int(data_split[0]) > 0:
                times = convert_to_spikelist(spike_times)
                params = {
                    'name': "SpikeTrain (SUA %s)" % (unit),
                    't_start': pq.Quantity(-300, units='ms', dtype=int),
                    't_stop': pq.Quantity(698, units='ms', dtype=int),
                    'times': pq.Quantity(times, units='ms', dtype=int),
                }

                yield (int(trial), int(unit), neo.SpikeTrain(**params))


    @classmethod
    def upload_session(cls, connection, doc, date, paths, lfp_channels,
                   sua_channels, conditions, colors, orientations, limit=None):
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
        :param lfp_channels:    list of electrode numbers (int)
        :param sua_channels:    list of SUA numbers (int)
        :param conditions:      list of behavioural conditions (str)
        :param colors:          list of stimulus colors (str)
        :param orientations:    list of stimulus orientations (str)
        :param limit:           limit the number of trials (int)
        :return:
        """

        # create common metadata
        metadata = cls.populate_session_metadata(date.strftime("%B %d, %Y"))
        metadata._parent = doc
        sync_obj_tree(connection, metadata, fail=True)

        # create trials (Neo Segments with odML Sections)
        block = cls.populate_dataset(
            "%s.dat" % date.strftime("%y%m%d"), lfp_channels, sua_channels
        )
        stimulus = filter(lambda x: x.type == 'Stimulus', metadata.sections)[0]
        with open(paths['lfp_cond'], 'r') as f:
            for i, l in enumerate(f):

                if not i % len(lfp_channels) == 0:  # len(lfp_channels)
                    continue

                trial, condition, color, orientation, channel = l.split(' ')
                if int(trial) > limit:
                    break

                section = cls.populate_stimulus_metadata(
                    trial, 1.3, conditions[int(condition)],
                    colors[int(color) - 1], orientations[int(orientation) - 1]
                )
                section._parent = stimulus
                stimulus.append(section)
                sync_obj_tree(connection, section, fail=True)

                segment = neo.Segment(
                    name='Trial %s (%s, %s, %s)' % (
                        trial, conditions[int(condition)],
                        colors[int(color) - 1],
                        orientations[int(orientation) - 1])
                )
                segment.metadata = section
                segment.block = block
                block.segments.append(segment)

        # read LFP data
        for trial, channel, signal in cls.read_lfp_data(paths):
            if trial > limit:
                break

            segment = block.segments[trial - 1]
            rc = block.recordingchannelgroups[0].recordingchannels[channel - 1]
            signal.segment = segment
            signal.recordingchannel = rc
            segment.analogsignals.append(signal)
            rc.analogsignals.append(signal)

        # read SUA data
        for trial, unit, spiketrain in cls.read_sua_data(paths):
            if trial > limit:
                break

            segment = block.segments[trial - 1]
            unit = block.recordingchannelgroups[0].units[unit - 1]
            spiketrain.segment = segment
            spiketrain.unit = unit
            segment.spiketrains.append(spiketrain)
            unit.spiketrains.append(spiketrain)

        sync_obj_tree(connection, block, fail=True)

        return metadata, block


