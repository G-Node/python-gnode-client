"""
Miscellaneous helper functions.
"""

import string
import random

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse


def id_from_location(location):
    if location.strip("/").endswith("/data"):
        location = location[0:len(location) - 5]
    ident = urlparse.urlparse(location).path.strip("/").split("/")[-1].lower()
    return ident


def random_str(length=20, prefix=None, separator="_"):
    rnd = "".join(random.choice(string.lowercase) for _ in range(length))
    if prefix is not None and len(prefix) > 0:
        rnd = prefix + separator + rnd
    return rnd
