================
General concepts
================

This chapter introduces some general concepts and functions of the Python G-Node Client such as session management,
configuration files and cache handling.

Creating a Session
==================

The following code example demonstrates how to create a new session object.
First a dictionary containing all connection parameters is created, which is later passed, along with other parameters,
to the constructor of the :py:class:`Session` class.

.. code-block:: python
    :linenos:

    from gnodeclient.session import Session

    options = {
        "location": "http://predata.g-node.org",
        "username": "user",
        "password": "secret",
        "cache_dir": "~/.gnodeclient/cache"
    }

    s = Session(options, file_name="~/gnodeclient/conf", persist_options=True)
    s.close()

Let's take a closer look on the connection parameters in the :py:obj:`options` dictionary:

:location:
    The is the base url of the G-Node REST API installation.
:username:
    The user to login with.
:password:
    The password used for authentication.
:cach_dir:
    This is the location, that will be used by the client to store cached objects. If this is not provided,
    the client will choose an appropriate system dependent location (e.g. ~/.cache/gnodeclient on Linux).

The two other parameters passed to the constructor are both related to the configuration of the client.
The parameter :py:obj:`file_name` sets the path to the configuration file, that stores the given connection
parameters and provides defaults if they are not set. If this parameter is None, the location will be
chosen by the client. If :py:obj:`persist_options` set to is True (default is False) the provided options
will be stored in the configuration file (except for password).

Assuming that a configuration file exists, it can be used to complement missing
connection parameters:

.. code-block:: python
    :linenos:

    s = Session({"password": "secret"}, file_name="~/gnodeclient/conf")

In the above example the location, username and cache_dir are retrieved from the file ~/gnodeclient/conf and then
used to establish the session.

The Global Session Object
=========================

For all use-cases where only one single session object is needed one can use the functions :py:func:`create` and
:py:func:`close` of the :py:mod:`gnodeclient.session` module.
Both functions operate on a global session object.
The subsequent example illustrates the use of them:

.. code-block:: python
    :linenos:

    from gnodeclient import session

    s1 = session.create(location="http://predata.g-node.org", username="user", password="secret", persist_options=True)
    s2 = session.create()
    id(s1) == id(s2)           # is True

    session.close()

The first call in line 3 creates the global session object and returns it.
The same object is then returned again by the second call of :py:func:`session.create`.
In the last line the global session is closed and destroyed, thus invalidating both session objects.

Caching
=======

The Python G-Node Client performs caching of remote objects.
Since the cache management is completely handled by the client, there is not much to learn about it for the user.
However, for some operations it is very useful to have some knowledge about how caching is used in order to understand
the behaviour of the client.

Here some general rules:

* The method :py:meth:`Session.select` always queries the remote server for its results.
* The method :py:meth:`Session.get` always returns results from the cache (if present) unless it is invoked with
  refresh True. In this case it will fetch data from the server if a newer version of the requested object is
  available.
* For performance reasons all lazy loaded objects are always retrieved from the cache and are only requested from
  the server when the object is missing from the cache.

There are mainly two methods, that give the user some control over the cache:

.. code-block:: python
    :linenos:

    block = s.get(block.location, refresh=True, recursive=True)
    # .. further operations

    s.clear_cache()
    # .. further operations

In line one, the :py:meth:`Session.get` method is invoked with both parameters refresh and recursive set to True.
This causes the block object to be updated and furthermore ensures that all its descendants are now present in
the cache with their most recent version.
Another way of making sure that only the most recent versions are used is to purge every cached object.
This is shown in line 4 of the above example.


Session Reference
=================

.. automodule:: gnodeclient.session
    :members:
