from distutils.core import setup

setup(
    name='GnodeClient',
    version='0.1',
    author='',
    author_email='',
    packages=['gnodeclient', 'gnodeclient.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/GnodeClient/',
    license='LICENSE.txt',
    description='Client for the G-Node REST API.',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 0.12.0",
        "simplejson >= 2.6.0"
    ],
)
