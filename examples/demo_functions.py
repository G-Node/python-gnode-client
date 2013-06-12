
# 1. init a session
from session import init
g = init()

# 2. ls function
g.ls()
g.ls('/mtd/sec/31/')

# 3. pull function
stimulus = g.pull('/mtd/sec/35/')
stimulus # odml section
stimulus.properties
stimulus.properties['Author'].values
stimulus.properties['Colors'].values
g.ls()

# 3. cd function
g.cd('/mtd/sec/31/')
g.ls()

# 4. explore dataset
g.ls('/eph/blk/7')
g.cd('/eph/blk/7')

# 5. quild a query
filt = {}
filt['block__id'] = 7
filt['color'] = 'blue'
filt['orientation'] = '135'
segs = g.select('segment', filt)
segs

# 6. get to know an id of a certain trial
segs[0]._gnode
[(s._gnode['date_created'], s._gnode['id']) for s in segs]

# 7. get the whole segment
s1 = g.pull('/eph/seg/167')
s1
s1.analogsignals
s1.metadata

# 8. plot selected segment
from matplotlib import pylab as pl
sigs = s1.analogsignals

pl.xlabel(sigs[0].times.units)
pl.ylabel(sigs[0].units)

for s in sigs:
    pl.plot(s.times, s)

pl.show()

