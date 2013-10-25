"""
Miscellaneous helper functions.
"""

import random

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse


def id_from_location(location):
    if location.strip("/").endswith("/data"):
        location = location[0:len(location) - 5]
    ident = urlparse.urlparse(location).path.strip("/").split("/")[-1]
    return ident


def random_str(length=16, prefix=None, separator="_", alphabet=None):
    if not alphabet:
        alphabet = "0123456789abcdefghijklmnopqrstuv"
    rnd = "".join(random.choice(alphabet) for _ in range(length))
    if prefix is not None and len(prefix) > 0:
        rnd = prefix + separator + rnd
    return rnd
