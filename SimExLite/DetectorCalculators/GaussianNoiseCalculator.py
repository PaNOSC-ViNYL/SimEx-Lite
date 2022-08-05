# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Gaussian Noise Detector Calculator Module"""

from libpyvinyl.BaseCalculator import BaseCalculator, Parameters
import SimExLite.DiffractionData as DD
import numpy as np
from tqdm import tqdm


def spliterate(buf, chunk):
    for start in range(0, len(buf), chunk):
        # print(start, start+chunk)
        yield buf[start: start + chunk]


class GaussianNoisePrameters(Parameters):
    """Gaussian noise parameters

    :param mu: The averange ADU for one photon
    :type mu: float
    :param sigs_popt: [slop, intercept]
    :type sigs_popt: list-like
    :param index: All the snapshots will be read by default.  Examples:
        * ``index=None``: read all the snapshots
        * ``index=0``: first snapshot
        * ``index=-2``: second to last
        * ``index=':'`` or ``index=slice(None)``: all
        * ``index='-3:'`` or ``index=slice(-3, None)``: three last
        * ``index='::2'`` or ``index=slice(0, None, 2)``: even
        * ``index='1::2'`` or ``index=slice(1, None, 2)``: odd
    :type index: int, slice or str
    :param poissionize: Whether to read the patterns with poission noise,
        defaults to ``false``.
    :type poissionize: bool, optional
    :param save_geom: Whether to save a crystFEL .geom file,
        defaults to ``True``.
    :type save_geom: bool, optional
    """

    def __init__(
        self,
        mu,
        sigs_popt,
        index=None,
        read_args: dict = {"poissonize": True},
        chunk_size: int = 10000,
    ):
        super().__init__()
        self.mu = mu
        self.sigs_popt = sigs_popt
        self.index = index
        self.read_args = read_args
        self.chunk_size = chunk_size


class GaussianNoiseCalculator(BaseCalculator):
    """Implement Gaussian noise to input diffraction data"""

    def __init__(self, input_path, parameters=None, dumpfile=None, output_path=None):
        """Constructor of the BaseCalcularor class."""
        super().__init__(
            parameters=parameters, dumpfile=dumpfile, output_path=output_path
        )
        self.input_path = input_path

    def backengine(self):
        """Method to do the actual calculation."""
        diffr_data = DD.read(
            self.input_path, self.parameters.index, **self.parameters.read_args
        )
        diffr_data.addGaussianNoise(self.parameters.mu, self.parameters.sigs_popt)
        print("Convert back to nphotons...", flush=True)
        chunk_size = self.parameters.chunk_size
        diffr_data.multiply(1 / self.parameters.mu, chunk_size)
        print("Get round values...", flush=True)
        for arr in tqdm(
            spliterate(diffr_data.array, chunk_size),
            total=int(np.ceil(float(len(diffr_data.array)) / chunk_size)),
        ):
            arr[:] = np.round(arr)
            arr[arr < 0] = 0
        diffr_data.setArrayDataType("i4")
        self._set_data(diffr_data)
        return 0

    def saveH5(self, format="emc"):
        """Save noised diffraction data as a HDF5 file

        :param format: What format to save the data in.
        :type format: str
        """
        DD.write(self.output_path, self.data, format)
