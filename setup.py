from distutils.core import setup

setup(
    name='gnodeclient',
    version='0.1.0',
    author='A. Stoewer, A. Sobolev',
    author_email='',
    packages=['gnodeclient', 'gnodeclient.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/GnodeClient/',
    license='LICENSE.txt',
    description='Client for the G-Node REST API.',
    long_description=open('README.rst').read(),
    install_requires=[
        "requests >= 0.12.0",
        "appdirs >= 1.2.0",
        "quantities >= 0.10.0",
        "neo >= 0.3.0",
        "requests-futures >= 0.9.0"
    ],
)
