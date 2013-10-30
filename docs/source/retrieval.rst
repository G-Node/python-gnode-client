========================
Get data from the G-Node
========================

This chapter explains with some more examples, how data can be retrieved from the G-Node REST API.
In all the following code examples we assume that an open session object :py:obj:`s` exists and that
the class :py:class:`Model` was imported.

The Select Function
===================

The purpose of the :py:meth:`Session.select` method is to retrieve a list of objects from a certain type from the
G-Node REST API.
See the documentation for a detailed description of the used `object model`_.
Further the :py:meth:`Session.select` methods provides the possibility to filter the result by various criteria.
At the moment only so called raw filters are supported. Raw filters consist of a list of key value pairs represented as
a python dictionary.
The following example illustrates some common use cases for filters:

.. code-block:: python
    :linenos:

    # splitting results
    signals = s.select(Model.ANALOGSIGNAL, {"offset": 0, "max_results": 100})
    signals = s.select(Model.ANALOGSIGNAL, {"offset": 0, "max_results": 100})

    # search for owner
    blocks = s.select(Model.BLOCK, {"owner": "bob"})

    # search for certain properties
    segments = s.select(Model.SEGMENT, {"name__icontains": "foo"})
    signals = s.select(Model.ANALOGSIGNAL, {"t_start": 0})

    # get all odML sections without a parent (root sections)
    sections = s.select(Model.SECTION, {"parent_section__isnull": 1})

    # combine filters
    # get the first hundred root sections that are owned by the user "bob"
    filers = {
        "parent_section__isnull": 1,
        "offset": 0,
        "max_results": 100,
        "owner": "bob"
    }
    sections = s.select(Model.SECTION, filters)

The basic syntax for raw filters is rather complex.
The documentation of the G-Node REST API describes how to `query data`_ from the server in detail.

Since the filters can not be evaluated locally, the :py:meth:`Session.select` method always requests data
from the server and never from the local cache.
Regarding performance this means, that :py:meth:`Session.select` is comparably slow, on the other hand it ensures
that the result always contains the most recent versions of objects.


The Get Function
================

In contrast to :py:meth:`Session.select` the :py:meth:`Session.get` method only returns one single object.
In order to do so, the client must know the type and id of an object.
This information is encoded in the location property of each object returned by the api.
Typical location strings have the following format <category>/<type>/<id> here are some examples:

- metadata/section/K6LO7NH133
- electrophysiology/segment/3GQP0BTS90

Without any other parameter :py:meth:`Session.get` will look up the requested object in the cache and return it.
Only if an object is missing from the cache it will be requested from the server.
If an object was not found at all :py:meth:`Session.get` returns :py:const:`None`.
The following example demonstrates this behaviour.

.. code-block:: python
    :linenos:

    # clear the cache
    s.clear_cache()

    # get the segment from the server (slow)
    segment = s.get("electrophysiology/segment/K6LO7NH133")

    # get the segment from the cache (fast)
    segment = s.get("electrophysiology/segment/K6LO7NH133")

    # lazy loading data from the server (slow)
    noof_signals = len(segment.analogsignals)

In some situations it is very useful to make sure that the most recent version of and object is returned, even if
a (potentially older) version was already cached.
For this purpose the method defines an optional parameter called :py:obj:`refresh`.
If this parameter is set to :py:const:`True` the client will check if there is a newer version on the server.
If this is not the case, the client will return the cached object.

.. code-block:: python
    :linenos:

    s.clear_cache()                                                         # clear the cache

    # get the segment from the server (slow)
    segment = s.get("electrophysiology/segment/K6LO7NH133", refresh=True)

    # check first for newer version and get the data from the cache (medium)
    segment = s.get("electrophysiology/segment/K6LO7NH133", refresh=True)

Using the refresh parameter as shown above, also speeds up the performance in cases where the most recent
version was already cached, but is still considerably slower than without.

When working with larger datasets it can be quite annoying when some operations are fast (due to caching) whereas
other operations take longer.
Therefore the :py:meth:`Session.get` method provides a third optional parameter, that can be used to make sure, that
certain objects are cached.

.. code-block:: python
    :linenos:

    # clear the cache
    s.clear_cache()

    # load the most recent version of the segment and all its descendants to the cache (very slow)
    segment = s.get("electrophysiology/segment/K6LO7NH133", refresh=True, recursive=True)

    # lazy loading is fast because it uses the cache
    noof_signals = len(segment.analogsignals)


Work with Signal Data
=====================

The next short example shows how signal data can be retrieved from the server and then plotted using matplotlib.

.. code-block:: python
    :linenos:

    from matplotlib import pylab

    segment = s.get("electrophysiology/segment/K6LO7NH133")
    signals = segment.analogsignals

    for s in signals:
        pylab.plot(s.times, s)

    pylab.xlabel(signals[0].times.units.dimensionality.string)
    pylab.ylabel(signals[0].units.dimensionality.string)

    pylab.show()

Get Permissions
===============

Every kind of object that is returned by :py:meth:`Session.get` of :py:meth:`Session.select` has its own security
settings.
Those settings can be obtained using the :py:meth:`Session.permissions` method.

.. code-block:: python
    :linenos:

    segment = s.get("electrophysiology/segment/K6LO7NH133")
    perms = s.permissions(segment)

.. external references
.. _query data: http://g-node.github.io/g-node-portal/key_functions/data_api/query.html
.. _object model: http://g-node.github.io/g-node-portal/key_functions/object_model.html
