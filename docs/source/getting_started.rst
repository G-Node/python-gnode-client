===============
Getting started
===============

The `G-Node REST-API`_ uses the odML data model for metadata and the neo data model for electrophysiology data.
Therefore those models are also used in this client library.
In order to ge a better understanding about both concepts it is recommended to familiarize yourself with the
`neo documentation`_ and the publication about odML: `A bottom-up approach to data annotation in neurophysiology`_.

Before you can use the G-Node client, you have import the :py:mod:`gnodeclient` package and connect to a genode server.

.. code-block:: python

    from gnodeclient import session, Model

    s = session.create(location="http://predate.g-node.org", username="user", password="pass")

Once you have a session object and the session object is open, you can retrieve some data from the G-Node server.

.. code-block:: python

    blocks = s.select(Model.BLOCK)

The variable blocks now contains all neo Block objects that are owned by or shared with you.
The method :py:meth:`Session.select` is used to query the R-Node REST API for objects of a certain type.
The type is determined by passing the model name of the object as first parameter to the :py:meth:`Session.select` method.
Further more select accepts filters, which can be used filter the results by certain criteria.

Since the G-Node client returns only slightly extended versions of the native neo and odML objects, working with them is
quite simple.
Lets examine the block a bit closer:

.. code-block:: python

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

    print str(block.section)
    print len(block.segments)
    print len(block.recordingchannelgroups)



.. external references
.. _G-Node REST-API: http://g-node.github.io/g-node-portal/
.. _odML: http://www.g-node.org/projects/odml
.. _neo documentation: http://neo.readthedocs.org/en/0.3.0/
.. _A bottom-up approach to data annotation in neurophysiology: http://www.frontiersin.org/neuroinformatics/10.3389/fninf.2011.00016/abstract

