=========================
Upload Data to the G-Node
=========================

So far this guide was mainly about how to connect to the G-Node REST API and retrieve data from the server.
But of course storing data on the server is also an important part of the workflow.
Therefore this topic will be covered by the following sections.
All code examples assume, that an open :py:class:`Session` object :py:obj:`s` exists and that the packages
:py:mod:`neo` and :py:mod:`odml` as well as the class :py:class:`Model` are imported.

Create Objects
==============

As mentioned in the previous chapter, all objects that are handled by the client are not pure neo or odml objects, but
contain additional information (such as the location) that is needed by the client in order to identify the object.
This has some serious consequences when it comes to object upload.
To demonstrate these consequences the following example shows how NOT to do it.
Let's assume we want to create and upload a block and then change the block afterwards and save those changes too.

.. code-block:: python
    :linenos:

    block = neo.Block("A cool block")      # Saves block as a new object
    s.set(block)

    block.name = "A really cool block"     # Saves block as a new object too!!
    s.set(block)

    block.location    # AttributeError: 'Block' object has no attribute 'location'

In the first two lines just happens what was to be expected: a new block with the name "A cool block" was crated and
uploaded to the server.
In line 5 we then changed the name of the block.
However, in line 6 some would probably expect that the previously uploaded block is now updated, but it is not.
Instead a new block with the name "A really cool block" was created on the server.
This is caused by the behaviour of all methods of :py:class:`Session` which do not have side-effects.
In this case this means that the :py:obj:`block` that is passed to :py:meth:`Session.set` remains unchanged.
To be more specific this means that :py:obj:`block` still has no location assigned to it.
But without a location the client must assume that the object is a newly created object.

The solution to this problem is quite simple: :py:meth:`Session.set` returns a new instance of the object that was
passed as the first parameter.
This new instance contains all information that is needed by the client in order to identify the
object as something that already exists on the server.

This example demonstrate how it should be done:

.. code-block:: python
    :linenos:
    :emphasize-lines: 2,6

    block = neo.Block("A cool block")
    block = s.set(block)
    block.location    # OK, it has a location

    block.name = "A really cool block"
    block = s.set(block)
    block.location    # OK, it has a location

A good way to avoid errors is to create and upload an object simultaneously:

.. code-block:: python
    :linenos:

    block = s.set(neo.Block("A cool block"))

The next example shows a more complex use-case, where a block, a segment and an analogsignal is created and uploaded
to the server:

.. code-block:: python
    :linenos:

    import quantities as pq
    import numpy as np

    # create a block and a segment
    block = s.set(neo.Block("Experiment One"))
    segment = s.set(neo.Segment("Trial 01", ))

    # associate the segment with block and save it
    segment.block = block
    segment = s.set(segment)

    # create a signal
    signal_data = pq.Quantity(np.random.rand(100), 'mV')
    t_start= 100 * pq.ms
    sampling_rate = 1 * pq.Khz
    signal = s.set(AnalogSignal(signal=signal_data, t_start=t_start, sampling_rate=sampling_rate)

    # associate the signal with the segment and save it again
    signal.segment = segment
    signal = s.set(signal)

Looking at this example more closely, it is worth to mention, that associations between entities can only be set on
the one-side of the one-to-many relationship. The code in the following example would have no effect.

.. code-block:: python
    :linenos:

    block.segments.append(segment)
    block = s.set(block)

Update Objects
==============

Updating existing objects works very similar as the creation of new objects.

.. code-block:: python
    :linenos:

    # get a block and a segment from the server
    block = s.get("electrophysiology/block/2DFA548ESC")
    segment = s.get("electrophysiology/segment/K6LO7NH133")

    # change the name of the segment and associate it with the block
    segment.name = "Trial 100"
    segment.block = block

    segment = s.set(segment)

.. TODO update/set permissions
.. TODO tagging of objects
