
# 1. init a session
from session import GNode
g = GNode()

# 2. ls function
g.ls()
g.ls('/mtd/sec/HNHB7OSSAM/')

# 3. cd function
g.cd('/mtd/sec/HNHB7OSSAM/')
g.ls()

# 4. pull function
stimulus = g.pull('/mtd/sec/TMDCSTMLK7/')
stimulus # odml section
stimulus.properties
stimulus.properties['Colors'].values
stimulus.properties['Orientations'].values
g.ls()

# 5. explore dataset
g.ls('/eph/blk/4M47OCTV0M/')

# 6. build a query for remote
filt = {}
filt['block'] = '4M47OCTV0M'
filt['color'] = '270'
filt['orientation'] = '135'
#filt['condition'] = 'saccade'
segs = g.select('segment', filt) # only segments, no data
len(segs)

# 7. get to know an id of a certain trial
segs[0]._gnode
[(s._gnode['fields']['date_created'], s._gnode['id']) for s in segs]

# 8. get the whole segment
s1 = g.pull('/eph/seg/R8KV2OP75L')
type(s1)
s1.analogsignals
s1.spiketrains
#s1.metadata # FIXME

# 9. pulled objects are cached
s1 = g.pull('/eph/seg/R8KV2OP75L')

# 10. only changed objects are pulled again
s1.analogsignals[0].name
s1.analogsignals[0]._gnode['location']
# change name here
s1 = g.pull('/eph/seg/R8KV2OP75L')
s1.analogsignals[0].name

# 11. you can fetch objects at previous states
a1 = g.pull('/eph/sig/IV57JQPFSL/', {"at_time": '2013-08-09 09:56:44'})
a1.name

# 12. cached objects are kept after a session brake
g.shutdown()
# quit here
from session import init
g = init()
s1 = g.pull('/eph/seg/R8KV2OP75L')

# 13. use of terminologies
g.terminologies
experiment = g.terminologies['Experiment'].clone()
experiment.name = 'Saccade and Fixation Tasks'
experiment.properties

# 14. local cache for new objects
g._cache.push(experiment, save=True)

# 15. find cached objects after session brake
# quit here
from session import init
g = init()
g._cache.ls()
experiment = g._cache.objects[5]

# 16. push function
g.push(experiment)
g.push(experiment, cascade=True)

# 17. sync only once if no changes
g.push(experiment, cascade=True)

# 18. query for analysis: for selected LFP channel, calculate the averages of  
# LFP traces over all trials for selected unique experimental condition (2 behav 
# cond, 4x4 stimuli). Save the averages because they will be used often. Plot 
# the LFP responses together with the mean for a given LFP channel, color, and 
# orientation.
query = {}

filt = {}
filt['block'] = '4M47OCTV0M'
filt['color'] = '270'
filt['orientation'] = '135'
segs = g.select('segment', filt) # only segments, no data

query['segment__in'] = [s._gnode['id'] for s in segs]

g.ls('/eph/blk/4M47OCTV0M/')
g.ls('/eph/rcg/L79SUDNQKU/')
query['recordingchannel'] = '1GGA033LPN'
len(sigs) = g.select('analogsignal', query, data_load=True)

# 19. plot selected data
from matplotlib import pylab as pl
for s in sigs:
    pl.plot(s.times, s)

pl.xlabel(sigs[0].times.units)
pl.ylabel(sigs[0].units)

pl.show()

#-------------------------------------------------------------------------------
# NOT IMPLEMENTED
#-------------------------------------------------------------------------------

# annotation

# delete

# sharing

# diff

from session import GNode
g = GNode()
experiment = g.terminologies['Experiment'].clone()
experiment.name = 'testing Datafiles 7'
d = g.models['datafile']('/tmp/bla.foo')
d.section = experiment
g.cache.push(experiment)
g.push(experiment, cascade=True)

# quick version history

# search of course (do we need it on the client?)

#-------------------------------------------------------------------------------
# ISSUES
#-------------------------------------------------------------------------------

# query local NEO objects

