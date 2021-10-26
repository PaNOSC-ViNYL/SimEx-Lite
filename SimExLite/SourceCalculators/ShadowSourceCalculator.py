# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Shadow Source Calculator Module"""

from libpyvinyl.BaseCalculator import BaseCalculator
from libpyvinyl.Parameters import CalculatorParameters


class ShadowSourceCalculator(BaseCalculator):
    """Shadow Source Calculator."""
    def __init__(self, name, parameters=None, dumpfile=None):
        # Constructor of the BaseCalcularor class.
        super().__init__(name, parameters=parameters, dumpfile=dumpfile)
        self.__init_user_parameters()
        self.__init_expert_parameters()

    def __init_user_parameters(self):
        """Initiate default parameters"""
        parameters = CalculatorParameters()
        parameters.new_parameter('photon_energy',
                                 unit='eV',
                                 comment='Beam photon energy')
        self.user_parameters = parameters

    def __init_expert_parameters(self):
        """Initiate expert parameters"""
        parameters = {}
        parameters['Name'] = 'My Name'
        self.expert_parameters = parameters

    def backengine(self):
        """ Method to do the actual calculation."""
        diffr_data = DD.read(self.input_path, self.parameters.index,
                             **self.parameters.read_args)
        diffr_data.addGaussianNoise(self.parameters.mu,
                                    self.parameters.sigs_popt)
        diffr_data.multiply(1 / self.parameters.mu)
        diffr_data.array = np.round(diffr_data.array)
        diffr_data.array[diffr_data.array < 0] = 0
        diffr_data.setArrayDataType('i4')
        self._set_data(diffr_data)
        return 0

    def saveH5(self, format='emc'):
        """Save noised diffraction data as a HDF5 file

        :param format: What format to save the data in.
        :type format: str
        """
        DD.write(self.output_path, self.data, format)
