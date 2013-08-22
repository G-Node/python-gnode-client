python-gnode-client
===================

python-gnode-client


Installation
------------

Install python-odml from https://github.com/G-Node/python-odml:

    $ git clone https://github.com/G-Node/python-odml.git
    $ cd python-odml
    $ sudo python setup.py install


Install python-neo from https://github.com/NeuralEnsemble/python-neo:

    $ git clone https://github.com/NeuralEnsemble/python-neo.git
    $ cd python-neo
    $ sudo python setup.py install


Install other packages:

    $ sudo aptitude install python-tables
    $ sudo aptitude install python-requests


Quickstart
----------

Edit the conf.json, set:

"host": "predata.g-node.org",
"port": 80

go to the python console:

$ python

or

$ ipython

initialize the session by:

    >>> from gnode.session import init
    >>> g = init()

use (session object) g to work with the remote.
