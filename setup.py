from setuptools import setup
from gnodeclient import GNODECLIENT_VERSION

with open("README.rst") as f:
    description_text = f.read()

with open("LICENSE.txt") as f:
    license_text = f.read()

setup(
    name="gnodeclient",
    version=GNODECLIENT_VERSION,
    author="A. Stoewer, A. Sobolev",
    author_email="adrian.stoewer@rz.ifi.lmu.de",
    packages=[
        "gnodeclient",
        "gnodeclient.model",
        "gnodeclient.store",
        "gnodeclient.test",
        "gnodeclient.util",
        "gnodeclient.result"
    ],
    package_dir={"gnodeclient": "gnodeclient"},
    package_data={"gnodeclient": [license_text, description_text]},
    test_suite="gnodeclient.test.test_all",
    #scripts=[],
    url="https://github.com/G-Node/python-gnode-client",
    license="LGPL",
    description="Client for the G-Node REST API.",
    include_package_data=True,
    long_description=description_text,
    install_requires=[
        "setuptools",
        "requests >= 0.12.0",
        "appdirs >= 1.2.0",
        "quantities >= 0.10.0",
        "neo >= 0.3.0",
        "requests-futures >= 0.9.0",
        "odml >= 1.0",
        "h5py >= 2.0.1"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
    ]
)
