"""
This examples are outdated and need to be adopted to the new client!!!

Before the start, you have to configure connection settings in conf.json file.

Use our DEMO user to get an overview:
{
    ...
    "username": "guest",
    "password": "pass",
    "host": "predata.g-node.org",
    "port": 80,
    ...
}

The data used below can be also explored at http://predata.g-node.org/wdat/

Please report any issues to support@g-node.org
"""

# init a session
from gnode.session import init
g = init()

# get familiar with supported object models
g.models # FIXME add Datafile?!

#-------------------------------------------------------------------------------
# Accessing data and metadata
#-------------------------------------------------------------------------------

# select objects of a certain type from the server
g.select('spiketrain', {'max_results': 10}) # returns python objects

# use some filters and parameters
g.select('spiketrain', {'name__icontains': '1104'}, mode='json')

# select fetches objects without resolving hierarchy to make it fast 
sections = g.select('section', {'name__icontains': 'stimulus'})

# get the full object with hierarchy resolution
stimulus = g.pull(sections[0])
stimulus # odML section
stimulus.properties # stimulus properties
stimulus.properties['Colors'].values
stimulus.properties['BehavioralConditions'].values

# select some dataset
blocks = g.select('block', {'max_results': 10})
blocks

# explore all time segments inside this dataset
segments = g.select('segment', {'block': blocks[0]})
segments

# query for only a subset of all segments
filt = {
    'block': blocks[0],
    'name__icontains': 'saccade'
}
segs = g.select('segment', filt) # selects only segments, no data
segs # note less segments fetched

# get one of the segments with all array data
s1 = g.pull(segs[0]) # note it fetches files with data
type(s1) # NEO segment
s1.analogsignals
s1.spiketrains
#s1.metadata # FIXME in development

# plot fetched signals
from matplotlib import pylab as pl
sigs = s1.analogsignals
for s in sigs:
    pl.plot(s.times, s)

pl.xlabel(sigs[0].times.units.dimensionality.string)
pl.ylabel(sigs[0].units.dimensionality.string)

pl.show()

#-------------------------------------------------------------------------------
# Create new data and metadata
#-------------------------------------------------------------------------------

project = g.select('section', {'name': 'DEMO'})[0] # please store all here

# use terminologies as template containers for key-value metadata
g.terminologies
experiment = g.terminologies['Experiment'].clone()
experiment.name = 'My custom experiment' # please don't change name
experiment.properties # a dict of key-values for metadata description
experiment.properties['Type'].value = 'electrophysiology'
project.append(experiment) # please store it in the DEMO section

# use NEO models to create data structure 
import quantities as pq

block = g.models['block'](name='DEMO dataset') # whole dataset

s = g.models['segment'](name='Trial 1') # new time segment
s.block = block # assign it to the dataset
block.segments.append(s)

data = [1.2345, 2.3456, 3.4567, 4.5678] * pq.mV # test data array
kwargs = {
    'name': 'Signal from neuron A',
    't_start': -300.0 * pq.ms,
    'sampling_rate': 500.0 * pq.Hz
}
signal = g.models['analogsignal'](data, **kwargs) # new time series
signal.segment = s # assign it to the time segment
s.analogsignals.append( signal )

# use local cache to save new objects on disk
g.cache.push(experiment, save=True)
g.cache.push(block, save=True) # all children objects are also saved

# find cached objects after session brake
g.cache.objects

# push objects to the server
g.push(experiment, cascade=False) # just push object without it's contents
g.push(experiment)
g.push(block)

#-------------------------------------------------------------------------------
# Upload raw file data
#-------------------------------------------------------------------------------

with open('/tmp/bla.foo', 'w') as f: # create a test file
    f.write('some test data')

# create new datafile inside metadata section
datafile = g.models['datafile']('/tmp/bla.foo', experiment)
g.push(experiment)

#-------------------------------------------------------------------------------
# Some useful features
#-------------------------------------------------------------------------------

project = g.select('section', {'name': 'DEMO'})[0]

# get a JSON representation of an object on the server
json_repr = getattr(project, '_gnode', None) # or just project._gnode

# get to know an ID of an object
json_repr['id']

#-------------------------------------------------------------------------------
# Caching
#-------------------------------------------------------------------------------

segs = g.select('segment', {'name__icontains': 'saccade'})
loc = segs[0]._gnode['location'] # you can pass location to the pull function
loc # remember ID to access object if session restart

# pulled objects are cached
s1 = g.pull(loc) # note the speed!

# only changed objects are pulled again
s1 = g.pull(loc) # fetches updates if any

# cached objects are kept after a session brake
# --- restart session here ---
s1 = g.pull(loc) # note the speed!

# synced objects can be also pulled from the cache
s1 == g.cache.pull(loc)

#-------------------------------------------------------------------------------
# Track changes
#-------------------------------------------------------------------------------

import datetime
now = datetime.datetime.now() # save current time for later

sections = g.select('section', {'name': 'My custom experiment'})
experiment = g.pull(sections[0])

# change object: note only changes pushed
experiment.name = 'My custom experiment CHANGED'
g.push(experiment) # note the speed!

# you can fetch objects at previous states
at_time = now.strftime('%Y-%m-%d %H:%M:%S')
test_exp = g.pull(experiment, {"at_time": at_time})
test_exp.name

#-------------------------------------------------------------------------------
# Explore objects on the remote
#-------------------------------------------------------------------------------

# output list of remote objects
from gnode.browser import Browser
b = Browser(g)
b.ls() # by default lists top metadata sections

# output objects of certain type
b.ls('section') # no objects, just output!

# output contents of an object
b.ls('/mtd/sec/HNHB7OSSAM/')

#-------------------------------------------------------------------------------
# IN DEVELOPMENT
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

