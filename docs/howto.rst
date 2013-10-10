How to install and use the python G-Node client
===============================================

About
-----

TODO write about the client

Requirements
------------

TODO write requirements

Install
-------

TODO write howto for installation

Usage
-----

Connect to the gnode server.

.. highlight::
    :linenos:

    from gnodeclient import *
    s = session.create()
    bls = s.select(Model.BLOCK)

