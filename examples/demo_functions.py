
# 1. init a session
from session import init
g = init()

# 2. ls function
g.ls()
g.ls('/mtd/sec/ACJKFO8I1E/')

# 3. pull function
stimulus = g.pull('/mtd/sec/E9DU7B5Q1D/')
stimulus # odml section
stimulus.properties
stimulus.properties['Author'].values
stimulus.properties['Orientations'].values
g.ls()

# 3. cd function
g.cd('/mtd/sec/ACJKFO8I1E/')
g.ls()

# 4. explore dataset
g.ls('/eph/blk/H7GCCA5O4J/')

# 5. build a query for remote
filt = {}
filt['block__id'] = 'H7GCCA5O4J'
filt['color'] = '270'
filt['orientation'] = '135'
segs = g.select('segment', filt)
segs

# 6. get to know an id of a certain trial
segs[0]._gnode
[(s._gnode['fields']['date_created'], s._gnode['id']) for s in segs]

# 7. get the whole segment
s1 = g.pull('/eph/seg/AV3MPA8FES')
s1
s1.analogsignals
s1.spiketrains
s1.metadata # FIXME

# 8. pulled objects are cached
s1 = g.pull('/eph/seg/AV3MPA8FES')

# 9. only changed objects are pulled again
s1.analogsignals[0].name
s1.analogsignals[0]._gnode['location']
# change name here
s1 = g.pull('/eph/seg/AV3MPA8FES')
s1.analogsignals[0].name

# 10. cached objects are kept after a session brake
g.shutdown()
g = init()
s1 = g.pull('/eph/seg/AV3MPA8FES')

# 11. plot selected segment
from matplotlib import pylab as pl
sigs = s1.analogsignals

pl.xlabel(sigs[0].times.units)
pl.ylabel(sigs[0].units)

for s in sigs:
    pl.plot(s.times, s)

pl.show()

# use of terminologies


# local cache for new objects

# find cached objects after session brake
g._cache.ls()
s1 = g._cache.objs[0]


# find cached objects after session brake

# sync function

# sync + only changes are synced

# query for analysis

# sharing

# query local NEO objects

