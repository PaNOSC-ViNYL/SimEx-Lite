# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

import os
from tqdm import tqdm
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from SimExLite.utils import isLegacySimExH5
from SimExLite.DataAPI.singfelDiffr import singfelDiffr
import SimExLite.DataAPI.EMCPhoton as EMC
import SimExLite.utils as utils

import argparse

data_type_dict = {
    '0': 'UNKOWN',
    '1': 'SIMEX SingFEL',
    '2': 'EMC Sparse Photon',
    '3': 'NeXus',
    '4': 'UNKOWN HDF5'
}


class DiffractionData:
    """The diffraction data class

    :param fn: The data file name
    :type fn: str
    :param keep_original: If keep the original data array, defaults to `True`. If set to
    `False`, all the changes will apply to func:`DiffractionData.array`.
    It's recommended to set it to `False` when the array is large.
    :type keep_original: bool, optional
    :param arr: The input data array when you want to create a new diffraction data
    :type arr: `np.numpy`, optional
    :param parameters: The input diffraction parameter dictionary when you want to
    create a new diffraction data
    :type parameters: dict
    """
    def __init__(self,
                 fn: str,
                 keep_original=True,
                 arr: np.array = None,
                 parameters=None) -> None:
        super().__init__()
        self.fn = fn
        self.keep_original = keep_original
        if arr is not None:
            # Writting mode
            self.__array = arr
        else:
            # Reading mode
            # Check if the file exists
            with open(self.fn, 'r') as f:
                f.close()
            self.type_id_read = getDataType(self.fn)
        if parameters is not None:
            self.parameters = parameters

    def getArray(self, index_range=None):
        """Get a numpy array of the diffraction data

        :param index_range: The indices of the diffraction patterns to dump to the numpy array,
        defaults to `None` meaning to take all the patterns. The array can be accessed by
        func:`DiffractionData.array`.
        :type index_range: list-like or `int`, optional
        """
        type_id_read = self.type_id_read
        if type_id_read == '0':
            raise TypeError("UNKNOWN data format.")
        elif type_id_read == '1':
            data = singfelDiffr(self.fn)
            data.getArray(index_range)
            self.__array = data.array

    def addBeamStop(self, stop_rad: int):
        """Add the beamstop in pixel radius to the diffraction patterns

        :param stop_rad: The radius of the beamstop in pixel unit
        :type stop_rad: int
        """
        processed = self.processed
        print("Adding beam stop...")
        for i, img in tqdm(enumerate(processed)):
            processed[i] = addBeamStop(img, stop_rad)

    def saveAs(self, data_format: str, file_name: str, save_original=False):
        """Save the diffraction data as a specific data_format

        :param data_format: The data format to save in.
        Supported formats:
            simple: A simple data array in hdf5
            singfel: SIMEX SingFEL
            emc: EMC Sparse Photon
        :type data_format: str
        :param file_name: The file name of the new data
        :type file_name: str
        :param save_original: If it's true, will the original array, instead of the processed
        one; defaults to False to save the processed array.
        :type save_original: bool
        """
        if save_original:
            array_to_save = self.array
        else:
            array_to_save = self.processed

        if data_format == "emc":
            print('writing {} to {}'.format(array_to_save.shape, file_name))
            data = []
            for img in tqdm(array_to_save):
                data.append(img.flatten())
            data = np.array(data)
            patterns = EMC.dense_to_PatternsSOne(data)
            patterns.write(file_name)
        elif data_format == "simple":
            utils.saveSimpleH5(array_to_save, file_name)
        else:
            raise TypeError("Unsupported format: ".format(data_format))

    @property
    def array(self):
        """The original pattern array"""
        try:
            return self.__array
        except AttributeError:
            raise AttributeError(
                "Please use DiffractionData.getArray() to get the array ready first."
            )

    @property
    def processed(self):
        """The processed pattern array"""
        try:
            if self.keep_original:
                return self.__processed
            else:
                return self.array
        except AttributeError:
            # Initialize the processed array
            self.__processed = np.copy(self.array)
            return self.__processed


def getDataType(fn) -> str:
    # Is hdf5?
    if h5py.is_hdf5(fn):
        if (isLegacySimExH5(fn)):
            with h5py.File(fn, 'r') as h5:
                idx = list(h5['data'].keys())[0]
                # If the h5 file has these keys
                if h5['data'][idx].keys() >= {'angle', 'data', 'diffr'}:
                    # SIMEX SingFEL
                    return "1"
                else:
                    print("This input file: {} contains no diffraction data".
                          format(fn))
                    return "0"
        else:
            # UNKOWN HDF5
            return "4"
    else:
        # UNKOWN DATA
        return "0"


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


def getPatternStatistic(img):
    """Get photon statistic info of a pattern

    :param img: Diffraction pattern
    :type img: np.2darray

    :return: (mean, max, min)
    :rtype: tuple
    """

    img_flat = img.ravel()
    mean_val = img_flat.mean()
    max_val = img_flat.max()
    min_val = img_flat.min()
    print('Mean: {}'.format(mean_val))
    print('Max: {}'.format(max_val))
    print('Min: {}'.format(min_val))

    return (mean_val, max_val, min_val)
