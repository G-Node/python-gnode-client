====================
Python G-Node Client
====================

The Python G-Node Client is a library, that provides access to the `G-Node REST-API`_
for the Python programming language.
The client provides a high-level interface to this service which includes useful features such as
lazy loading, caching and the prevention of so called lost updates.
Further more this client library can handle native neo and odml objects.


Dependencies
============

Using the G-Node Client requires some other python packages to be installed:

- neo_ A package for representing electrophysiology data in Python
- quantities_ Arithmetic and conversions of physical quantities
- odml_ Open metadata markup language
- appdirs_ Get appropriate platform-specific user dirs
- request-futures_ Asynchronous Python HTTP Request
- h5py_ HDF5 for Python

In order to build the documentation and install the package using setup.py the following
packages are recommended.

- sphinx_
- setuptools_

All dependencies with the exception of the python odml package, can be installed
using easy_install.
On debian bases linux distributions one install packages for quantities (python-quantities),
neo (python-neo), sphinx (python-sphinx), setuptools (python-setuptools) and h5py (python-h5py)
using the package manager (apt-get, aptitude).

To install the odml package use the following commands, with appropriate permissions
(e.g. with sudo for the last command).

.. code-block:: guess

    git clone https://github.com/G-Node/python-odml.git
    cd python-odml
    python setup.py install


Install
=======

To install the client invoke the following commands using appropriate permissions.

.. code-block:: guess

    git clone https://github.com/G-Node/python-gnode-client.git
    cd python-gnode-client
    python setup.py install


Howto use the client
====================

More information about how to use the client can be found in the online documentation_.

If this packages sphinx_ and setuptools_ are installed on your system, the documentation can
also be build from the cloned repository by executing the following command:

.. code-block:: guess

    python setup.py build_sphinx


.. TODO add link to github pages here

.. external references
.. _documentation: http://g-node.github.io/python-gnode-client/
.. _neo: http://neuralensemble.org/neo/
.. _quantities: https://github.com/python-quantities/python-quantities
.. _odml: https://github.com/G-Node/python-odml
.. _appdirs: https://github.com/ActiveState/appdirs
.. _request-futures: https://github.com/ross/requests-futures
.. _h5py: http://www.h5py.org/
.. _G-Node REST-API: http://g-node.github.io/g-node-portal/
.. _sphinx: http://sphinx-doc.org/
.. _setuptools: https://pypi.python.org/pypi/setuptools

