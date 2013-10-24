================
General concepts
================


Session management
==================

Connect to the gnode server.

.. code-block:: python

    from gnodeclient import *
    s = session.create()
    bls = s.select(Model.BLOCK)


Session Reference
=================

.. automodule:: gnodeclient.session
    :members:
