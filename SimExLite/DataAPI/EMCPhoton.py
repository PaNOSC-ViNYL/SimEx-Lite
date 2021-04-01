# -*- coding: future_fstrings -*-
# Copyright (C) 2021 Juncheng E, Shen Zhou (National University of Singapore)
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""EMCPhoton module to read and write a EMC photon sparse binary file"""

import os
from pathlib import Path
import numpy as np
import h5py
import matplotlib.pylab as plt
import matplotlib.colors as colors
from scipy.sparse import csr_matrix


class PatternsSOne:
    """A class to store the EMC photon sparse data. `Format introduction
    <https://github.com/duaneloh/Dragonfly/wiki/Data-stream-simulator#make_data>`_

    :param num_pix: Number of pixels per pattern
    :type num_pix: int
    :param ones: Number of one-photon events in each pattern
    :type ones: numpy.1darray
    :param multi: Number of multi-photon events in each pattern
    :type multi: numpy.1darray
    :param place_ones: The locations of the single photon pixels in each pattern
    :type place_ones: numpy.1darray
    :param place_multi: The locations of the multiple photon pixels in each pattern
    :type place_multi: numpy.1darray
    :param count_multi: Number of photons in each of those multiple photon pixels
    :type count_multi: numpy.1darray
    """
    ATTRS = ["ones", "multi", "place_ones", "place_multi", "count_multi"]

    def __init__(
            self,
            num_pix: int,
            ones: np.ndarray,
            multi: np.ndarray,
            place_ones: np.ndarray,
            place_multi: np.ndarray,
            count_multi: np.ndarray,
    ) -> None:
        self.num_pix = num_pix
        self._ones = ones
        self._multi = multi
        self._place_ones = place_ones
        self._place_multi = place_multi
        self._count_multi = count_multi
        self._ones_idx = np.zeros(self.num_data + 1, dtype=self._ones.dtype)
        np.cumsum(self._ones, out=self._ones_idx[1:])
        self._multi_idx = np.zeros(self.num_data + 1, dtype=self._multi.dtype)
        np.cumsum(self._multi, out=self._multi_idx[1:])

    def __len__(self):
        return self.num_data

    @property
    def num_data(self):
        return len(self._ones)

    @property
    def shape(self):
        """Return (number_of_patterns, number_of_pixels_per_pattern)"""
        return self.num_data, self.num_pix

    def write(self, path) -> None:
        with Path(path).open("wb") as fptr:
            header = np.zeros((256), dtype="i4")
            header[:2] = [self.num_data, self.num_pix]
            header.tofile(fptr)
            for g in PatternsSOne.ATTRS:
                self.attrs(g).astype("i4").tofile(fptr)

    def attrs(self, g):
        if g == "ones_idx":
            return self._ones_idx
        if g == "multi_idx":
            return self._multi_idx
        if g == "ones":
            return self._ones
        if g == "multi":
            return self._multi
        if g == "place_ones":
            return self._place_ones
        if g == "place_multi":
            return self._place_multi
        if g == "count_multi":
            return self._count_multi
        raise ValueError(f"What is {g}?")

    def _get_sparse_ones(self) -> csr_matrix:
        _one = np.ones(1, "i4")
        _one = np.lib.stride_tricks.as_strided(  # type: ignore
            _one,
            shape=(self._place_ones.shape[0], ),
            strides=(0, ))
        return csr_matrix((_one, self._place_ones, self._ones_idx),
                          shape=self.shape)

    def _get_sparse_multi(self) -> csr_matrix:
        return csr_matrix(
            (self._count_multi, self._place_multi, self._multi_idx),
            shape=self.shape)

    def todense(self) -> np.ndarray:
        """
        To dense ndarray
        """
        return np.squeeze(self._get_sparse_ones().todense()
                          + self._get_sparse_multi().todense())


def dense_to_PatternsSOne(arr: np.ndarray) -> PatternsSOne:
    """Convert diffraction pattern array data to EMC sparse data

    :param arr: A multi-snapshot array with diffraction patterns flattened
    :type arr: np.2darray

    :return: EMC photon sparse data
    :rtype: PatternsSOne
    """
    mask_one = arr == 1
    mask_multi = arr > 1
    place_ones = np.where(mask_one)[1]
    pmask, place_multi = np.where(mask_multi)  # pmask: pattern mask
    return PatternsSOne(
        arr.shape[1],
        np.sum(mask_one, axis=1, dtype=np.int32),
        np.sum(mask_multi, axis=1, dtype=np.int32),
        place_ones.astype(np.int32),
        place_multi.astype(np.int32),
        arr[pmask, place_multi].astype(np.int32),
    )


def parse_bin_PatternsSOne(fn: str):
    """Parse a EMC sparse binary file

    :param fn: The name of the sparse binary file
    :type fn: str

    :return: EMC photon sparse data
    :rtype: PatternsSOne
    """
    path = Path(fn)
    with path.open("rb") as fin:
        num_data = np.fromfile(fin, dtype=np.int32, count=1)[0]
        start, end = 0, num_data
        num_pix = np.fromfile(fin, dtype=np.int32, count=1)[0]
        fin.seek(1024)
        ones = np.fromfile(fin, dtype=np.int32, count=num_data)
        multi = np.fromfile(fin, dtype=np.int32, count=num_data)
        fin.seek(4 * ones[:start].sum(), os.SEEK_CUR)
        place_ones = np.fromfile(fin,
                                 dtype=np.int32,
                                 count=ones[start:end].sum())
        fin.seek(4 * (ones[end:].sum() + multi[:start].sum()), os.SEEK_CUR)
        sum_multi = multi[start:end].sum()
        place_multi = np.fromfile(fin, dtype=np.int32, count=sum_multi)
        fin.seek(4 * (multi[end:].sum() + multi[:start].sum()), os.SEEK_CUR)
        count_multi = np.fromfile(fin, dtype=np.int32, count=sum_multi)
        fin.seek(4 * multi[end:].sum(), os.SEEK_CUR)
        if fin.read(1):
            raise Exception(f"Error when parsing {fn}")
    ones = ones[start:end]
    multi = multi[start:end]
    return PatternsSOne(
        num_pix,
        ones,
        multi,
        place_ones,
        place_multi,
        count_multi,
    )


def plotEMCPhoton(fn, idx=0, shape=None, log_scale=True):
    """Plot a pattern from a EMC file

    :param idx: The index of the pattern to plot
    :type idx: int
    :param shape: The array shape of the diffraction pattern
    :type shape: int, optional
    """
    sPattern = parse_bin_PatternsSOne(fn)
    print('num_pix:', sPattern.num_pix)
    data = sPattern.todense()
    if not shape:
        shape = (-1, int(np.sqrt(sPattern.num_pix)))
    if log_scale is True:
        plt.imshow(data[idx].reshape(shape), norm=colors.LogNorm())
    else:
        plt.imshow(data[idx].reshape(shape))
    plt.colorbar()
    plt.show()


def main(input_file, output_file):
    print('converting', input_file, 'to', output_file)
    data = []
    with h5py.File(input_file, "r") as fp:
        dp = fp['data']
        for fidx in sorted(dp.keys()):  # fidx: frame index
            data.append(dp[fidx]['data'][...].flatten())
        data = np.array(data)
    patterns = dense_to_PatternsSOne(data)
    print(patterns.shape)
    print('writing')
    patterns.write(output_file)
