# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

from libpyvinyl.BaseCalculator import BaseCalculator, Parameters
from SimExLite.DiffractionData import DiffractionData


class gaussianNoisePrameters(Parameters):
    """Gaussian noise parameters

    :param mu: The averange ADU for one photon
    :type mu: float
    :param sigs_popt: [slop, intercept]
    :type sigs_popt: list-like
    :param index_range: The indices of the diffraction patterns to dump to the numpy array,
    defaults to `None` meaning to take all the patterns. The array can be accessed by
    func:`DiffractionData.array`.
    :type index_range: list-like or `int`, optional
    :param poissionize: Whether to read the patterns with poission noise,
    defaults to false.
    :type poissionize: bool, optional
    """
    def __init__(self, mu, sigs_popt, index_range=None, poissonize=False):
        super().__init__()
        self.mu = mu
        self.sigs_popt = sigs_popt
        self.index_range = index_range
        self.poissonize = poissonize


class gaussianNoiseCalculator(BaseCalculator):
    """Implement Gaussian noise to input diffraction data"""
    def __init__(self,
                 input_path,
                 parameters=None,
                 dumpfile=None,
                 output_path=None):
        """ Constructor of the RandomImageCalculator class. """
        super().__init__(parameters=parameters,
                         dumpfile=dumpfile,
                         output_path=output_path)
        self.input_path = input_path

    def backengine(self):
        """ Method to do the actual calculation."""
        diffr_data = DiffractionData()
        diffr_data.read(self.input_path, self.parameters.index_range)
        diffr_data.createArray()
        diffr_data.addGaussianNoise(self.parameters.mu,
                                    self.parameters.sigs_popt)
        self._set_data(diffr_data)
        return 0

    def saveH5(self, data_format='simple'):
        """Save noised diffraction data as a HDF5 file

        :param data_format: What format to save the data in.
        :type data_format: str
        """
        try:
            self.data.saveAs(data_format, self.output_path)
        except TypeError:
            raise TypeError("Unrecognized output_path")

    def saveEMC(self):
        """Save noised diffraction data in a EMC sparse photon file"""

        try:
            self.data.saveAs('emc', self.output_path)
        except TypeError:
            raise TypeError("Unrecognized output_path")
