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
    """
    def __init__(self, mu, sigs_popt):
        super().__init__()
        self.mu = mu
        self.sigs_popt = sigs_popt


class gaussianNoise(BaseCalculator):
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
        diffr_data = DiffractionData(self.input_path, keep_original=False)
        diffr_data.addGaussianNoise(self.parameters.mu,
                                    self.parameters.sigs_popt)
        self.__data = diffr_data
        return 0

    def saveH5(self, data_format='simple'):
        """Save noised diffraction data as a HDF5 file

        :param data_format: What format to save the data in.
        :type data_format: str
        """
        self.data.saveAs(data_format, self.output_path)
