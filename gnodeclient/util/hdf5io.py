"""
This module provides easy to use functions for reading and writing datasets
to and from the root of an HDF5 file.
"""

import numpy


def store_array_data(path, array_data):
    """
    Write an array to the the first dataset of an HDF5 file.

    :param path: The full path to the HDF5 file.
    :type path: str
    :param array_data: The array data to store.
    :type array_data: numpy.ndarray|list
    """
    # TODO Datafile: implement store_array_data
    pass


def read_array_data(path):
    """
    Read array data from the first dataset of an HDF5 file.

    :param path: The full path to the HDF5 file.
    :type path: str

    :returns: The array read from the file.
    :rtype: numpy.ndarray|list
    """
    # TODO Datafile: implement read_array_data
    return numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
