"""
Before the start, you have to configure connection settings in conf.json file.

Use our demo user to get an overview:
{
    ...
    "username": "guest",
    "password": "pass",
    "host": "predata.g-node.org",
    "port": 80,
    ...
}

Same data can be explored at http://predata.g-node.org/wdat/

Please report any issues to support@g-node.org
"""

# 1. init a session
from gnode.session import init
g = init()

# get familiar with supported object models
g.models # FIXME add Datafile?!

#-------------------------------------------------------------------------------
# Accessing data and metadata
#-------------------------------------------------------------------------------

# select objects of a certain type
g.select('spiketrain', {'max_results': 10}) # returns python objects

# use some filters and parameters
g.select('spiketrain', {'name__icontains': '1104'}, mode='json')

# select fetches objects without contents to make it fast 
sections = g.select('section', {'name__icontains': 'stimulus'})

# to get the full object use pull
stimulus = g.pull(sections[0])
stimulus # odML section
stimulus.properties # stimulus properties
stimulus.properties['Colors'].values
stimulus.properties['BehaviouralConditions'].values

# select some dataset
blocks = g.select('block', {'max_results': 10})

# explore time segments inside dataset
segments = g.select('segment', {'block': blocks[0]})

# query for only a subset of all segments
filt = {}
filt['block'] = blocks[0]
filt['name__icontains'] = 'saccade'
segs = g.select('segment', filt) # only segments, no data

# 8. get one of the segments with all array data
s1 = g.pull(segs[0]) # note it fetches files with data
type(s1) # NEO segment
s1.analogsignals
s1.spiketrains
#s1.metadata # FIXME in development

# FIXME add some plotting here

#-------------------------------------------------------------------------------
# Caching features
#-------------------------------------------------------------------------------

# 9. pulled objects are cached
s1 = g.pull('/eph/seg/R8KV2OP75L') # note the speed!

# 10. only changed objects are pulled again
s1 = g.pull('/eph/seg/R8KV2OP75L') # fetches updates if any

# 12. cached objects are kept after a session brake
# --- restart session here ---
s1 = g.pull('/eph/seg/R8KV2OP75L') # note the speed!

#-------------------------------------------------------------------------------
# Create new data and metadata
#-------------------------------------------------------------------------------

# XXX create demo data in the DEMO section! easy to delete

# 13. use terminologies as containers for key-value metadata
g.terminologies
experiment = g.terminologies['Experiment'].clone()
experiment.name = 'Saccade and Fixation Tasks'
experiment.properties

# 14. local cache for new objects
g._cache.push(experiment, save=True)

# 15. find cached objects after session brake
# --- restart session here ---
g._cache.ls()
experiment = g._cache.objects[5]

# 16. push object to the server
g.push(experiment) # just object without it's contents
g.push(experiment, cascade=True)


# XXX  upload files
from session import GNode
g = GNode()
experiment = g.terminologies['Experiment'].clone()
experiment.name = 'testing Datafiles 7'
d = g.models['datafile']('/tmp/bla.foo')
d.section = experiment
g.cache.push(experiment)
g.push(experiment, cascade=True)

#-------------------------------------------------------------------------------
# Track changes
#-------------------------------------------------------------------------------

# 17. push only changes
import datetime
now = datetime.datetime.now()
experiment.name = 'Saccade and Fixation Tasks, V1'
g.push(experiment, cascade=True)

# 11. you can fetch objects at previous states
a1 = g.pull('/eph/sig/IV57JQPFSL/', {"at_time": '2013-08-09 09:56:44'})
a1.name

#-------------------------------------------------------------------------------
# Build more complex queries
#-------------------------------------------------------------------------------

# for selected LFP channel, calculate the averages of  
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
# Explore objects on the remote
#-------------------------------------------------------------------------------

# 2. output remote objects
from gnode.browser import Browser
b = Browser(g)
b.ls() # by default lists top metadata sections

# 3. output objects of certain type
b.ls('analogsignal') # no objects, just output!

# 4. output contents of an object 
b.ls('/mtd/sec/HNHB7OSSAM/')


#-------------------------------------------------------------------------------
# Some advanced features
#-------------------------------------------------------------------------------

# 7. get to know an id of a certain trial
segs[0]._gnode
[(s._gnode['fields']['date_created'], s._gnode['id']) for s in segs]


#-------------------------------------------------------------------------------
# NOT IMPLEMENTED
#-------------------------------------------------------------------------------

# annotation

# delete

# sharing

# diff

# quick version history

# search of course (do we need it on the client?)

#-------------------------------------------------------------------------------
# ISSUES
#-------------------------------------------------------------------------------

# query local NEO objects

