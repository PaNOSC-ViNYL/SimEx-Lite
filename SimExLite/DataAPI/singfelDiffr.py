# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""singfelDiffr module to read and write a singfel diffr output data"""
import numpy as np
import h5py
import matplotlib.pyplot as plt
from tqdm import tqdm


class singfelDiffr:
    """A Singfel diffr data class

    :input_path: The path of the input file name
    :input_path: str
    """
    def __init__(self,
                 input_path: str,
                 index_range=None,
                 poissonize=False) -> None:
        self.input_path = input_path
        self.parameters = getParameters(self.input_path)
        self.index_range = index_range
        self.poissonize = poissonize
        self.indices = getIndices(self.input_path, self.index_range)
        self.pattern_type = getPatternType(self.poissonize)

    def createArray(self, index_range=None, poissonize=False):
        """Get a numpy array of the diffraction data, the array can be accessed by
        func:`singfelDiffr.array`. `index_range` and `poissonize` of the class can
        be reset here.

        :param index_range: The indices of the diffraction patterns to dump to the numpy array,
        defaults to `None` meaning to take all the patterns.
        :type index_range: list-like or `int`, optional
        :param poissionize: Whether to read the patterns with poission noise,
        defaults to false.
        :type poissionize: bool, optional
        """
        path = self.input_path

        if index_range == self.index_range:
            indices = self.indices
        else:
            indices = getIndices(path, index_range)
            # Reset the class indices
            self.indices = indices

        if poissonize == self.poissonize:
            pattern_type = self.pattern_type
        else:
            pattern_type = getPatternType(poissonize)
            # Reset the class pattern_type
            self.pattern_type = pattern_type

        with h5py.File(path, 'r') as h5:
            arr_size = len(indices)
            pattern_shape = self.pattern_shape
            arr = np.zeros((arr_size, pattern_shape[0], pattern_shape[1]))

            try:
                # Flush to print it before tqdm
                print('Creating the array...', flush=True)
                for i, ix in enumerate(tqdm(indices)):
                    root_path = '/data/%s/' % (ix)
                    path_to_data = root_path + pattern_type
                    arr[i] = h5[path_to_data][...]
            except KeyError:
                indices_tmp = [key for key in h5['data'].keys()]
                print('The first few existed indices: {}'.format(
                    indices_tmp[:3]))
                raise KeyError('Cannot find pattern index: {}'.format(ix))

        self.__array = arr

    @property
    def iterator(self):
        """Return the iterator of diffraction data"""
        path = self.input_path
        indices = self.indices
        pattern_type = self.pattern_type

        with h5py.File(path, 'r') as h5:
            for ix in indices:
                root_path = '/data/%s/' % (ix)
                path_to_data = root_path + pattern_type
                diffr = h5[path_to_data][...]

                yield diffr

    @property
    def array(self):
        """Diffraction pattern numpy array"""
        return self.__array

    @property
    def pattern_shape(self):
        """The array shape of a pattern in the hdf5 file"""
        with h5py.File(self.input_path, 'r') as h5:
            group_name = list(h5['data'].keys())[0]
            return h5['data'][group_name]['diffr'].shape

    @property
    def pattern_total(self):
        """The total number of diffraction patterns in the hdf5 file"""
        with h5py.File(self.input_path, 'r') as h5:
            npattern = len(h5['data'])
        return npattern

    def __set_solid_angles(self):
        """ Solid angle of each pixel """
        """ Note: the pixel is assumed to be square """

        # pixel number (py, px)
        pn = self.parameters['geom']['mask'].shape
        # initialize array
        solidAngles = np.zeros_like(pn)
        y, x = np.indices(pn)
        # pixel size (meter)
        ph = self.parameters['geom']['pixelHeight']
        pw = self.parameters['geom']['pixelWidth']
        # sample to detector distance (meter)
        s2d = self.parameters['geom']['detectorDist']

        center_x = 0.5 * (pn[1] - 1)
        center_y = 0.5 * (pn[0] - 1)
        rx = (x - center_x) * pw
        ry = (y - center_y) * ph
        r = np.sqrt(rx**2 + ry**2)
        pixDist = np.sqrt(r**2 + s2d**2)
        alpha = np.arctan2(pw, 2 * pixDist)
        solidAngles = 4 * np.arcsin(np.sin(alpha)**2)
        self.__solid_angles = solidAngles

    @property
    def solid_angles(self):
        try:
            return self.__solid_angles
        except AttributeError:
            self.__set_solid_angles()
            return self.__solid_angles

    def plotSolidAngles(self):
        plt.figure()
        plt.imshow(self.solid_angles)
        plt.colorbar()
        plt.show()

    def __set_q_map(self):
        """ q of each pixel (unit: 1/A)"""
        """ q = 4*pi*sin(twotheta/2)/lmd """

        # pixel number (py, px)
        pn = self.parameters['geom']['mask'].shape
        # initialize array
        qMap = np.zeros_like(pn)
        y, x = np.indices(pn)
        # pixel size (meter)
        ph = self.parameters['geom']['pixelHeight']
        pw = self.parameters['geom']['pixelWidth']
        # sample to detector distance (meter)
        s2d = self.parameters['geom']['detectorDist']

        E0 = self.parameters['beam']['photonEnergy']
        lmd = 12398 / E0  # Angstrom

        center_x = 0.5 * (pn[1] - 1)
        center_y = 0.5 * (pn[0] - 1)
        rx = (x - center_x) * pw
        ry = (y - center_y) * ph
        r = np.sqrt(rx**2 + ry**2)
        twotheta = np.arctan2(r, s2d)
        qMap = 4 * np.pi * np.sin(twotheta / 2) / lmd

        self.__q_map = qMap

    @property
    def q_map(self):
        try:
            return self.__q_map
        except AttributeError:
            self.__set_q_map()
            return self.__q_map

    def plotQMap(self):
        plt.figure()
        plt.imshow(self.q_map)
        plt.colorbar()
        plt.show()


def getPatternType(poissonize):
    if poissonize:
        pattern_type = 'data'
    else:
        pattern_type = 'diffr'
    return pattern_type


def getIndices(input_path, index_range=None):
    """Get a list of indices of diffraction patterns in a Singfel HDF5 file.

    :param input_path: The input path of the HDF5 file
    :type input_path: str
    :param index_range: The indices of the diffraction patterns to dump to the numpy array,
    defaults to `None` meaning to take all the patterns.
    :type index_range: list-like or `int`, optional

    :return: ReturnDescription
    :rtype: ReturnType
    """
    index_range = index_range
    with h5py.File(input_path, 'r') as h5:
        if index_range is None:
            indices = list(h5['data'].keys())
            # Sort to get the correct order of the frames
            indices.sort()
        else:
            try:
                indices = ["%0.7d" % ix for ix in index_range]
            # If index_range is a int
            except TypeError:
                indices = ["{:07}".format(index_range)]

    return indices


def getParameters(input_path):
    """Get a dictionary of the beam parameters and geometry parameters in a Singfel Diffr
    HDF5 file.
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
