===============
Getting started
===============

The `G-Node REST-API`_ uses the odML data model for metadata and the neo data model for electrophysiology data.
Therefore those models are also used in this client library.
In order to get a better understanding about both concepts it is recommended to familiarize yourself with the
`neo documentation`_ and the publication about odML: `A bottom-up approach to data annotation in neurophysiology`_.

The best way to follow this getting started guide ist to start python in interactive mode or ipython and try out
the following code examples.
Before you can use the G-Node client, you have import the :py:mod:`gnodeclient` package and connect to an instance of a G-Node server.
If you don't have a local installation you may use credentials from the example below.
Since we need the neo package later on, we also include this.

.. code-block:: python
    :linenos:

    import neo
    from gnodeclient import session, Model

    s = session.create(location="http://predata.g-node.org", username="user", password="pass")

Once you have a session object and the session object is open, you can retrieve some data from the G-Node server.

.. code-block:: python
    :linenos:

    blocks = s.select(Model.BLOCK)

The variable blocks now contains all neo Block objects that are owned by or shared with you.
The method :py:meth:`Session.select` is used to query the G-Node REST API for objects of a certain type.
The type is determined by passing the model name of the object as first parameter to the :py:meth:`Session.select` method.
Furthermore select accepts filters, which can be used filter the results by certain criteria.

Since the G-Node client returns only slightly extended versions of the native neo and odML objects, working with them is
quite simple.
Lets examine the block a bit closer:

.. code-block:: python
    :linenos:

    block = blocks[0]
    print block.name
    print block.description
    print block.location

As normal :py:class:`neo.Block` objects the block returned by the session has a name and a description.
But in addition it has also a property called location.
This is one of the minor extensions that are introduced by the client.
The location is an identifier that allows the client library to identify the corresponding remote entity of the object.

Additionally to normal properties :py:class:`Block` objects have relationships to other objects like :py:class:`Section`,
:py:class:`Segment` and :py:class:`RecordingChannelGroup`.
For objects returned by methods of the :py:class:`Session` class, properties representing those relationships are
initialized with lazy-loading proxies.
This means, that related objects are only downloaded or fetched from the cache, when the respective properties of the
object are accessed for the first time.
The following piece of code illustrates this behaviour.

.. code-block:: python
    :linenos:

    print type(block.segments)
    print len(block.segments)
    print len(block.recordingchannelgroups)

The output of line one will show, that :py:attr:`Block.segments` is a proxy object.
As soon as data from the proxy is requested (line 2 and 3) the data will be fetched from the server or the cache.

The :py:meth:`Session.select` method is used to get data by type and provides the possibility to reduce the results by filter.
A second method for getting data is :py:meth:`Session.get`.
This method takes a single object identifier, the location, as first argument.

.. code-block:: python
    :linenos:

    block = s.get(block.location, refresh=True)

The parameter refresh controls whether or not the client should check for updates on the server if the object was
found in the cache.

The next code example demonstrates how to upload data to the G-Node server via REST API.
First a new :py:class:`neo.Segment` is created and in a second step the segment is added to the segments of an existing
block.

.. code-block:: python
    :linenos:

    segment = neo.Segment("cool segment")
    segment.block = block

    segment = s.set(segment)

    block = s.get(block.location, refresh=True)

The above example reveals some design principles of the G-Node API and the client library:

1. Associations between objects can only be changed on the one-side of the one-to-many relationship.
2. All functions of the client interface are free of side-effects.
   This means, that existing objects are never changed by subsequent function calls.
   In this example the content of :py:attr:`block.segments` changes when the segment was saved using :py:meth:`Session.set`.
   Since the original block object is not changed by this method, the block has to be updated (line 6).





.. external references
.. _G-Node REST-API: http://g-node.github.io/g-node-portal/
.. _odML: http://www.g-node.org/projects/odml
.. _neo documentation: http://neo.readthedocs.org/en/0.3.0/
.. _A bottom-up approach to data annotation in neurophysiology: http://www.frontiersin.org/neuroinformatics/10.3389/fninf.2011.00016/abstract

