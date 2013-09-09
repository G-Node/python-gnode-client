"""
Basic test data
"""

from random import random, randint, randrange

import numpy as np
import quantities as pq

from neo import Block, Segment, EventArray

from gnode.utils import generate_id


def singleton(cls):
    """
    Singleton implementation (http://www.python.org/dev/peps/pep-0318/#examples)
    """

    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


def r_str(prefix, length=5):
    return prefix + '_' + generate_id(length)


def r_length():
    return randint(10, 1000)


def r_times(length=None):
    if length is not None:
        length = r_length()
    return np.array([random() * 1000 for _ in xrange(length)]) * pq.s


def r_labels(length=None):
    if length is not None:
        length = r_length()
    return np.array([r_str("label") for _ in xrange(length)], dtype='S')


class TestData(object):
    """
    Unified store for test data
    """

    def __init__(self, base_location, missing_id, test_data, existing_data=None):
        self.base_location = base_location
        self.missing_id = missing_id
        self.test_data = test_data
        self.existing_data = existing_data


@singleton
class TestDataCollection(object):
    """
    A simple singleton collection of test data
    """

    def __init__(self):
        self.__data_sets = {}

        loc = "/electrophysiology/block/"
        miss = generate_id()
        data = Block(name=r_str("block"), description=r_str("desc"))
        self["block"] = TestData(loc, miss, data)

        loc = "/electrophysiology/segment/"
        miss = generate_id()
        data = Segment(name=r_str("segment"), description=r_str("desc"))
        self["segment"] = TestData(loc, miss, data)

        loc = "/electrophysiology/eventarray/"
        leng = r_length()
        miss = generate_id()
        data = EventArray(times=r_times(leng), labels=r_labels(leng), name=r_str("eventarray"),
                          description=r_str("desc"))
        self["eventarray"] = TestData(loc, miss, data)

    def __getitem__(self, item):
        return self.__data_sets[item]

    def __setitem__(self, key, value):
        if isinstance(value, TestData):
            self.__data_sets[key] = value
        else:
            raise ValueError("The value is not from the type TestData: %s!" % str(value))

    def __len__(self):
        return len(self.__data_sets)

    def __iter__(self):
        return iter(self.__data_sets)

    def __str__(self):
        return str(self.__data_sets)

    def __repr__(self):
        return repr(self.__data_sets)
