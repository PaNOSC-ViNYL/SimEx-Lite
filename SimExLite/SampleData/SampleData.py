# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Sample Structure Data APIs"""
import h5py
# import ase


class MolecularDynamicsData:
    """Molecular Dynamics Data class

    :param input_path: Path to data file
    :type input_path: str
    """
    def __init__(self, input_path=None):
        self.input_path = input_path
        self.file_format = self.__getFileFormat()

    def __getFileFormat(self) -> str:
        """ Check the file format.
        HDF5:
            openPMD-MD
            XMDYN
        ASCII:
            Handled by ASE

        """
        if h5py.is_hdf5(self.input_path):
            with h5py.File(self.input_path, 'r') as h5:
                try:
                    version = h5['/info/package_version'][()].decode('ascii')
                except KeyError:
                    return "UNKNOWN"
                if version.find('XMDYN') != -1:
                    return "XMDYN"
                else:
                    return "UNKNOWN"

