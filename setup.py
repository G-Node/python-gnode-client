import gnodeclient

from distutils.core import setup

setup(
    name='gnodeclient',
    version=gnodeclient.__version__,
    author='A. Stoewer, A. Sobolev',
    author_email='',
    packages=['gnodeclient', 'gnodeclient.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/GnodeClient/',
    license='LICENSE.txt',
    description='Client for the G-Node REST API.',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 0.12.0",
        "simplejson >= 2.6.0",
        "appdirs >= 1.2.0",
        "fcache >= 0.3.0",
        "quantities >= 0.10.0",
        "neo >= 0.3.0",
        "requests-futures >= 0.9.0"
        "ProxyTypes >= 0.9"
    ],
)
