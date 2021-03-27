# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""singfelDiffr module to read and write a singfel diffr output data"""
import numpy as np
import h5py
from tqdm import tqdm


class singfelDiffr:
    """A Singfel diffr data class

    :input_path: The path of the input file name
    :input_path: str
    """
    def __init__(self, input_path: str) -> None:
        self.input_path = input_path
        self.parameters = getParameters(self.input_path)

    def getArray(self, index_range=None, poissonize=False):
        """Get a numpy array of the diffraction data

        :param index_range: The indices of the diffraction patterns to dump to the numpy array,
        defaults to `None` meaning to take all the patterns. The array can be accessed by
        func:`singfelDiffr.array`.
        :type index_range: list-like or `int`, optional
        :param poissionize: Whether to read the patterns with poission noise
        :type poissionize: bool, optional
        """
        pattern_list = []
        with h5py.File(self.input_path, 'r') as h5:
            if index_range is None:
                indices = [key for key in h5['data'].keys()]
            else:
                try:
                    indices = ["%0.7d" % ix for ix in index_range]
                # If index_range is a int
                except TypeError:
                    indices = ["{:07}".format(index_range)]
            if poissonize:
                pattern_type = 'data'
            else:
                pattern_type = 'diffr'

            try:
                print('Loading patterns...')
                for ix in tqdm(indices):
                    root_path = '/data/%s/' % (ix)
                    path_to_data = root_path + pattern_type
                    pattern_list.append(h5[path_to_data][...])
            except KeyError:
                indices_tmp = [key for key in h5['data'].keys()]
                print('The first few existed indices: {}'.format(
                    indices_tmp[:3]))
                raise KeyError('Cannot find pattern index: {}'.format(ix))

        self.__array = np.array(pattern_list)

    @property
    def array(self):
        """Diffraction pattern numpy array"""
        return self.__array

    @property
    def pattern_total(self):
        """The total number of diffraction patterns in the hdf5 file"""
        with h5py.File(self.input_path, 'r') as h5:
            npattern = len(h5['data'])
        return npattern


def getParameters(input_path):
    """Get a dictionary of the beam parameters and geometry parameters in a Singfel Diffr
    hdf5 file.

    :param paramName: ParamDescription
    :type paramName: paramType

    :return: ReturnDescription
    :rtype: ReturnType
    """

    # Setup return dictionary.
    parameters_dict = {'beam': {}, 'geom': {}}

    # Open file.
    with h5py.File(input_path, 'r') as h5:
        # Loop over entries in /params.
        for top_key in ['beam', 'geom']:
            # Loop over groups.
            for key, val in h5['params/%s' % (top_key)].items():
                # Insert into return dictionary.
                parameters_dict[top_key][key] = val[()]
    # Return.
    return parameters_dict
