from setuptools import setup, find_packages

with open("README.rst") as f:
    description_text = f.read()

with open("LICENSE.txt") as f:
    license_text = f.read()

setup(
    name="gnodeclient",
    version="0.3.1",
    author="A. Stoewer, A. Sobolev",
    author_email="adrian.stoewer@rz.ifi.lmu.de",
    packages=find_packages(),
    package_dir={"gnodeclient": "gnodeclient"},
    test_suite="gnodeclient.test.test_all",
    scripts=[],
    url="https://github.com/G-Node/python-gnode-client",
    license="LGPL",
    description="Client for the G-Node REST API.",
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
    ],
    package_data={"gnodeclient": [license_text, description_text]},
    include_package_data=True,
    zip_safe=False,
)
