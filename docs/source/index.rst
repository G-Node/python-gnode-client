How to install and use the python G-Node client
===============================================

About
-----

TODO write about the client

Usage
-----

Connect to the gnode server.

.. code-block:: python

    from gnodeclient import *
    s = session.create()
    bls = s.select(Model.BLOCK)

Session Reference
-----------------

.. automodule:: gnodeclient.session
   :members:

