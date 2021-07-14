# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""singfelDiffr module to read and write a singfel diffr output data"""
import numpy as np
import h5py
from tqdm import tqdm
from SimExLite.utils.io import parseIndex
import SimExLite


def iread(filename, index=None, poissonize=True):
    """Iterator for reading diffraction patterns from a file."""
    index = parseIndex(index)
    pattern_type = getPatternType(poissonize)
    with h5py.File(filename, 'r') as h5:
        data_grp = h5['data']
        data_list = list(data_grp)
        data_list.sort()
        indices = data_list[index]

        for i in indices:
            yield data_grp[i][pattern_type][...]


def read(filename, index=None, poissonize=True) -> np.array:
    """Read diffraction patterns into an array from a file."""
    # Flush to print it before tqdm
    index = parseIndex(index)
    arr_size = len(range(getPatternTotal(filename))[index])
    pattern_shape = getPatternShape(filename)
    arr = np.zeros((arr_size, pattern_shape[0], pattern_shape[1]))
    if isinstance(index, (slice, str)):
        with tqdm(total=arr_size) as progress_bar:
            for i, pattern in enumerate(iread(filename, index, poissonize)):
                arr[i] = pattern
                progress_bar.update(1)  # update progress
        return arr
    else:
        # If only reading one pattern
        return next(iread(filename, index, poissonize))


def write(filename,
          arr,
          detector_counts,
          detector_intensity,
          quaternion,
          det,
          beam,
          method_desciption=''):
    prepH5(filename)
    # Method Description
    with h5py.File(filename, 'a') as f:
        for i, pattern in enumerate(arr):
            group_name = '/data/' + '{0:07}'.format(i + 1) + '/'
        f.create_dataset('info/method_description',
                         data=np.string_(method_desciption))


def prepH5(filename):
    """
    Create output file, prepare top level groups, write metadata.
    """
    with h5py.File(filename, 'w') as f:
        # Generate top level groups
        f.create_group('data')
        f.create_group('params')
        f.create_group('misc')
        f.create_group('info')

        # Write metadata
        # Package format version
        f.create_dataset('info/package_version',
                         data=np.string_('SimExLite' + SimExLite.__version__))
        # Contact
        f.create_dataset('info/contact',
                         data=np.string_('{} <{}>'.format(
                             SimExLite.__author__, SimExLite.__email__)))
        # Data Description
        f.create_dataset(
            'info/data_description',
            data=np.string_(
                'This dataset contains diffraction patterns written using SimEx singfelDiffr API.'
            ))
        # Data format version
        f.create_dataset('version', data=np.string_('0.2'))


def getPatternTotal(filename):
    """Get the total number of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, 'r') as h5:
        npattern = len(h5['data'])
    return npattern


def getPatternShape(filename):
    """Get the shape of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, 'r') as h5:
        group_name = list(h5['data'])[0]
        return h5['data'][group_name]['diffr'].shape


def getPatternType(poissonize):
    if poissonize:
        pattern_type = 'data'
    else:
        pattern_type = 'diffr'
    return pattern_type


def getParameters(filename):
    """Get a dictionary of the beam parameters and geometry parameters in a Singfel Diffr
    HDF5 file.
    """

    # Setup return dictionary.
    parameters_dict = {'beam': {}, 'geom': {}}

    # Open file.
    with h5py.File(filename, 'r') as h5:
        # Loop over entries in /params.
        for top_key in ['beam', 'geom']:
            # Loop over groups.
            for key, val in h5['params/%s' % (top_key)].items():
                # Insert into return dictionary.
                parameters_dict[top_key][key] = val[()]
    # Return.
    return parameters_dict


#     def __set_solid_angles(self):
#         """ Solid angle of each pixel """
#         """ Note: the pixel is assumed to be square """

#         # pixel number (py, px)
#         pn = self.parameters['geom']['mask'].shape
#         # initialize array
#         solidAngles = np.zeros_like(pn)
#         y, x = np.indices(pn)
#         # pixel size (meter)
#         ph = self.parameters['geom']['pixelHeight']
#         pw = self.parameters['geom']['pixelWidth']
#         # sample to detector distance (meter)
#         s2d = self.parameters['geom']['detectorDist']

#         center_x = 0.5 * (pn[1] - 1)
#         center_y = 0.5 * (pn[0] - 1)
#         rx = (x - center_x) * pw
#         ry = (y - center_y) * ph
#         r = np.sqrt(rx**2 + ry**2)
#         pixDist = np.sqrt(r**2 + s2d**2)
#         alpha = np.arctan2(pw, 2 * pixDist)
#         solidAngles = 4 * np.arcsin(np.sin(alpha)**2)
#         self.__solid_angles = solidAngles

#     def __set_q_map(self):
#         """ q of each pixel (unit: 1/A)"""
#         """ q = 4*pi*sin(twotheta/2)/lmd """

#         # pixel number (py, px)
#         pn = self.parameters['geom']['mask'].shape
#         # initialize array
#         qMap = np.zeros_like(pn)
#         y, x = np.indices(pn)
#         # pixel size (meter)
#         ph = self.parameters['geom']['pixelHeight']
#         pw = self.parameters['geom']['pixelWidth']
#         # sample to detector distance (meter)
#         s2d = self.parameters['geom']['detectorDist']

#         E0 = self.parameters['beam']['photonEnergy']
#         lmd = 12398 / E0  # Angstrom

#         center_x = 0.5 * (pn[1] - 1)
#         center_y = 0.5 * (pn[0] - 1)
#         rx = (x - center_x) * pw
#         ry = (y - center_y) * ph
#         r = np.sqrt(rx**2 + ry**2)
#         twotheta = np.arctan2(r, s2d)
#         qMap = 4 * np.pi * np.sin(twotheta / 2) / lmd

#         self.__q_map = qMap

#     @property
#         try:

#             return self.__q_map
#         except AttributeError:
#             self.__set_q_map()
#             return self.__q_map

#     def plotQMap(self):
#         plt.figure()
#         plt.imshow(self.q_map)
#         plt.colorbar()
#         plt.show()