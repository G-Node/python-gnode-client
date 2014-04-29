"""
Miscellaneous helper functions.
"""

import random
import string

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse


def id_from_location(location):
    return urlparse.urlparse(location).path.strip("/").split("/")[4]


def random_str(length=16, prefix=None, separator="_", alphabet=None):
    if not alphabet:
        alphabet = "0123456789abcdefghijklmnopqrstuv"
    rnd = "".join(random.choice(alphabet) for _ in range(length))
    if prefix is not None and len(prefix) > 0:
        rnd = prefix + separator + rnd
    return rnd


def random_base32(length=10):
    alphabet = tuple(list('0123456789' + string.ascii_uppercase)[:32])
    uid = random.choice(alphabet[1:])
    for i in range(length - 1):
        uid += random.choice(alphabet)
    return uid