import odml
import datetime
from gnodeclient import session
from gnodeclient.examples.use_case_core import UseCase

path_generator = lambda x: {
    'lfp_data': "/data/spike_lfp/full/%s/lfp%sdata.dat" % (x, x),
    'lfp_cond': "/data/spike_lfp/full/%s/lfp%scond.dat" % (x, x),
    'sua_data': "/data/spike_lfp/full/%s/sua%sdata.dat" % (x, x),
    'sua_cond': "/data/spike_lfp/full/%s/sua%scond.dat" % (x, x)
}

conditions = ["Fixation", "Saccade"]
colors = ["0 deg (red)", "90 deg (blue)", "180 deg (green)", "270 deg (yellow)"]
orientations = ["0 deg", "45 deg", "90 deg", "135 deg"]

#-------------------------------------------------------------------------------

g = session.create(
    location="http://beta.g-node.org", username="demo", password="pass"
)

doc = g.set(odml.Document(author='Thomas Wachtler', version="1.0"))

# session 080707
date = datetime.date(2008, 7, 7)
paths = path_generator(date.strftime("%y%m%d"))
lfp_channels = [1, 2, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16]
sua_channels = [13, 13, 14, 9, 9]
UseCase.upload_session(
    g, doc, date, paths, lfp_channels, sua_channels, conditions, colors,
    orientations, limit=5
)

# session 080708
date = datetime.date(2008, 7, 8)
paths = path_generator(date.strftime("%y%m%d"))
lfp_channels = [1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]
sua_channels = [11, 12, 13]
UseCase.upload_session(
    g, doc, date, paths, lfp_channels, sua_channels, conditions, colors,
    orientations, limit=5
)

# session 080709
date = datetime.date(2008, 7, 9)
paths = path_generator(date.strftime("%y%m%d"))
lfp_channels = [1, 2, 4, 5, 6, 9, 10, 12, 13, 14, 15]
sua_channels = [13, 13, 15, 15, 4, 4, 5, 5]
UseCase.upload_session(
    g, doc, date, paths, lfp_channels, sua_channels, conditions, colors,
    orientations, limit=5
)


if 0:  # not implemented yet

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

