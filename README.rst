====================
Python G-Node Client
====================

The Python G-Node Client is a library, that provides access to the `G-Node REST-API`_
for the Python programming language.
The client provides a high-level interface to the REST API which includes usefull features such as
lazy loading, caching and the prevention of so called lost updades.
Further more this client liabrary can handle native neo and odml objects.


Dependencies
============

Using the G-Node Client requires some other python packages to be installed:

1. neo_ A package for representing electrophysiology data in Python
2. quantities_ Arithmetic and conversions of physical quantities
2. odml_ Open metadata markup language
3. appdirs_ Get appropriate platform-specific user dirs
4. request-futures_ Asynchronous Python HTTP Request
5. h5py_ HDF5 for Python

All dependencies with the exception of the python odml package, can be installed
using easy_install.
On debian bases linux distributions one install packages for quantities (python-quantities),
neo (python-neo) and h5py (python-h5py) using apt-get or aptitude.

To install the odml package use the following commands:

.. code-block:: bash

    git clone https://github.com/G-Node/python-odml.git
    cd python-odml
    sudo python setup.py install


Install
=======

How to install the client

.. code-block:: bash

    git clone https://github.com/G-Node/python-gnode-client.git
    cd python-gnode-client
    sudo python setup.py install


Howto use the client
====================

How to use the client from ipyhon


.. external references
.. _neo: http://neuralensemble.org/neo/
.. _quantities: https://github.com/python-quantities/python-quantities
.. _odml: https://github.com/G-Node/python-odml
.. _appdirs: https://github.com/ActiveState/appdirs
.. _request-futures: https://github.com/ross/requests-futures
.. _h5py: http://www.h5py.org/
.. _G-Node REST-API: http://g-node.github.io/g-node-portal/
