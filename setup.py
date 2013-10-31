try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open("README.rst") as file:
    long_description = file.read()

packages = [
    "gnodeclient",
    "gnodeclient.model",
    "gnodeclient.store",
    "gnodeclient.test",
    "gnodeclient.util",
    "gnodeclient.result"
]

requires = [
    "requests >= 0.12.0",
    "appdirs >= 1.2.0",
    "quantities >= 0.10.0",
    "neo >= 0.3.0",
    "requests-futures >= 0.9.0",
    "odml >= 1.0",
    "h5py >= 2.0.1"
]

setup(
    name="gnodeclient",
    version="0.2.0",
    author="A. Stoewer, A. Sobolev",
    author_email="adrian.stoewer@rz.ifi.lmu.de",
    packages=packages,
    package_dir={"gnodeclient": "gnodeclient"},
    package_data={"gnodeclient": ["LICENSE.txt", "README.rst"]},
    test_suite="gnodeclient.test.test_all",
    scripts=[],
    url="https://github.com/G-Node/python-gnode-client",
    license="LGPL",
    description="Client for the G-Node REST API.",
    include_package_data=True,
    long_description=long_description,
    install_requires=requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2"
    ]
)
