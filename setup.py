try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from gnodeclient import GNODECLIENT_VERSION

with open('README.rst') as file:
    long_description = file.read()

with open('LICENSE.txt') as file:
    license_text = file.read()

setup(
    name='gnodeclient',
    version=GNODECLIENT_VERSION,
    author='A. Stoewer, A. Sobolev',
    author_email='adrian.stoewer@rz.ifi.lmu.de',
    packages=[
        'gnodeclient',
        'gnodeclient.model',
        'gnodeclient.store',
        'gnodeclient.test',
        'gnodeclient.util'
    ],
    test_suite="gnodeclient.test.test_all",
    scripts=[],
    url='http://pypi.python.org/pypi/GnodeClient/',
    license=license_text,
    description='Client for the G-Node REST API.',
    long_description=long_description,
    install_requires=[
        "requests >= 0.12.0",
        "appdirs >= 1.2.0",
        "quantities >= 0.10.0",
        "neo >= 0.3.0",
        "requests-futures >= 0.9.0",
        "odml",
        "h5py >= 2.0.1"
    ],
)
