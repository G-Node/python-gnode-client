# encoding: utf-8
"""
Class for "reading" fake data from an imaginary file.

For the user, it generates a :class:`Segment` or a :class:`Block` with a
sinusoidal :class:`AnalogSignal`, a :class:`SpikeTrain` and an
:class:`EventArray`.

For a developer, it is just an example showing guidelines for someone who wants
to develop a new IO module.

Depends on: scipy

Supported: Read

Author: sgarcia

"""
from __future__ import absolute_import

from session import init

# I need to subclass BaseIO
from neo.io.baseio import BaseIO
from neo.description import *

# to import from core
from neo.core import Block, Segment, AnalogSignal, SpikeTrain, EventArray

# some tools to finalize the hierachy
from neo.io.tools import create_many_to_one_relationship

# note neo.core needs only numpy and quantities
import numpy as np
import quantities as pq

# but my specific IO can depend on many other packages
from numpy import pi, newaxis
import datetime
try:
    have_scipy = True
    from scipy import stats
    from scipy import randn, rand
    from scipy.signal import resample
except ImportError:
    have_scipy = False

try:
    import simplejson as json

except ImportError:
    import json


all_objects = list(class_by_name.values())
all_objects.remove(Block)  # the order is important
all_objects = [Block] + all_objects


class GNodeIO(BaseIO):
    """
    Class for "reading" fake data from an imaginary file.

    For the user, it generates a :class:`Segment` or a :class:`Block` with a
    sinusoidal :class:`AnalogSignal`, a :class:`SpikeTrain` and an
    :class:`EventArray`.

    For a developer, it is just an example showing guidelines for someone who wants
    to develop a new IO module.

    Two rules for developers:
      * Respect the Neo IO API (:ref:`neo_io_API`)
      * Follow :ref:`io_guiline`

    Usage:
        >>> from neo import io
        >>> r = io.ExampleIO(filename='itisafake.nof')
        >>> seg = r.read_segment(lazy=False, cascade=True)
        >>> print(seg.analogsignals)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [<AnalogSignal(array([ 0.19151945,  0.62399373,  0.44149764, ...,  0.96678374,
        ...
        >>> print(seg.spiketrains)    # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
         [<SpikeTrain(array([ -0.83799524,   6.24017951,   7.76366686,   4.45573701,
            12.60644415,  10.68328994,   8.07765735,   4.89967804,
        ...
        >>> print(seg.eventarrays)    # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [<EventArray: TriggerB@9.6976 s, TriggerA@10.2612 s, TriggerB@2.2777 s, TriggerA@6.8607 s, ...
        >>> anasig = r.read_analogsignal(lazy=True, cascade=False)
        >>> print(anasig._data_description)
        {'shape': (150000,)}
        >>> anasig = r.read_analogsignal(lazy=False, cascade=False)

    """

    is_readable = True # This class can only read data
    is_writable = False # write is not supported

    # This class is able to directly or indirectly handle the following objects
    # You can notice that this greatly simplifies the full Neo object hierarchy
    supported_objects  = all_objects

    # This class can return either a Block or a Segment
    # The first one is the default ( self.read )
    # These lists should go from highest object to lowest object because
    # common_io_test assumes it.
    readable_objects    = all_objects
    # This class is not able to write objects
    writeable_objects   = [ ]

    has_header         = False
    is_streameable     = False

    # This is for GUI stuff : a definition for parameters when reading.
    # This dict should be keyed by object (`Block`). Each entry is a list
    # of tuple. The first entry in each tuple is the parameter name. The
    # second entry is a dict with keys 'value' (for default value),
    # and 'label' (for a descriptive name).
    # Note that if the highest-level object requires parameters,
    # common_io_test will be skipped.
    read_params = {}

    # do not supported write so no GUI stuff
    write_params       = None

    name               = 'G-Node I/O'

    extensions          = [ 'gnode' ]

    # mode can be 'file' or 'dir' or 'fake' or 'database'
    # the main case is 'file' but some reader are base on a directory or a database
    # this info is for GUI stuff also
    mode = 'database'



    def __init__(self , filename = None) :
        """


        Arguments:
            filename : the filename

        Note:
            - filename is here just for exampe because it will not be take in account
            - if mode=='dir' the argument should be dirname (See TdtIO)

        """
        BaseIO.__init__(self)
        self.filename = filename

        self.config = json.load( open(self.filename, 'r') )
        self.session = init(self.config['config_path'], self.config['models_path'])

    def read_all_blocks(self, lazy=False, cascade=True, **kargs):
        """
        Loads all blocks from G-Node.
        """
        blocks = []

        for location in self.config['blocks']:
            blocks.append( self.session.pull( location ) )

        return blocks






