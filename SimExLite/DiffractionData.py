"""Diffraction Data APIs"""

import os
from pathlib import Path
import numpy as np
import h5py
import matplotlib.pylab as plt
import matplotlib.colors as colors
from scipy.sparse import csr_matrix
from SimExLite.utils import isLegacySimExH5
import argparse

data_type_dict = {
    '0': 'UNKOWN',
    '1': 'Legacy SIMEX Singfel',
    '2': 'EMC Sparse Photon',
    '3': 'Legacy Photon'
}


class DiffractionData:
    def __init__(self, input_path: str) -> None:
        super().__init__()
        self.input_path = input_path

    def getArray(self, index_range=None):
        type_id = getDataType(self.input_path)
        if type_id == '0':
            raise TypeError("UNKNOWN data format.")
        elif type_id == '1':
            return

    @property
    def array(self):
        try:
            return self.__array
        except AttributeError:
            self.__array = self.getArray()


def getDataType(fn):
    # Is hdf5?
    if h5py.is_hdf5(fn):
        if (isLegacySimExH5(fn)):
            with h5py.File(fn, 'r') as h5:
                idx = list(h5['data'].keys())[0]
                # If the h5 file has these keys
                if h5['data'][idx].keys() >= {'angle', 'data', 'diffr'}:
                    # Legacy SIMEX Singfel
                    return "1"


def addBeamStop(img, stop_rad):
    """Add the beamstop in pixel radius to diffraction pattern

    :param img: Diffraction pattern
    :type img: np.2darray
    :param stop_rad: The radius of the beamstop in pixel unit
    :type stop_rad: int

    :return: Beamstop masked 2D array
    :rtype: np.2darray
    """
    stop_mask = np.ones_like(img)
    center = np.array(img.shape) // 2
    y = np.indices(img.shape)[0] - center[0]
    x = np.indices(img.shape)[1] - center[1]
    r = np.sqrt((x * x + y * y))
    stop_mask[r <= stop_rad] = 0
    masked = img * stop_mask
    return masked
