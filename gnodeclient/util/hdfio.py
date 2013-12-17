"""
This module provides easy to use functions for reading and writing datasets
to and from the root of an HDF5 file.
"""

import numpy as np
import h5py

def store_array_data(path, array_data):
    """
    Write an array to the the first dataset of an HDF5 file.

    :param path: The full path to the HDF5 file.
    :type path: str
    :param array_data: The array data to store.
    :type array_data: numpy.ndarray|list
    """
    if not isinstance(array_data, np.ndarray):
        array_data = np.array(array_data)

    f = h5py.File(path, 'w')
    f.create_dataset('arraydata', data=array_data)
    f.close()


def read_array_data(path):
    """
    Read array data from the first dataset of an HDF5 file.

    :param path: The full path to the HDF5 file.
    :type path: str

    :returns: The array read from the file.
    :rtype: numpy.ndarray|list
    """
    try:
        with h5py.File(path, 'r') as f:
            return f[f.keys()[0]].value
    except IOError:
        return None