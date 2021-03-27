# Copyright (C) 2021 Juncheng E 
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

from libpyvinyl.BaseCalculator import BaseCalculator, Parameters
import numpy
import h5py
import sys

class DetectorGaussianNoiseCalculator(BaseCalculator):
    """ class: Implements simulation of a rondom image for demonstration purposes. """
    def __init__(self, parameters=None, dumpfile=None, input_path=None, output_path=None):
        """ Constructor of the RandomImageCalculator class. """
        super().__init__(parameters=parameters, dumpfile=dumpfile, output_path=output_path)

    def backengine(self):
        """ Method to do the actual calculation."""
        tmpdata = numpy.random.random((self.parameters.grid_size_x, self.parameters.grid_size_y))

        self._set_data(tmpdata)
        return 0

    def saveH5(self, openpmd=False):
        """ Save image to hdf5 file 'output_path'. """
        with h5py.File(self.output_path, "w") as h5:
            ds = h5.create_dataset("/data", data=self.data)

            h5.close()
