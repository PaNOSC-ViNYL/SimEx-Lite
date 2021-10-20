# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""singfelDiffr module to read and write a singfel diffr output data"""
import numpy as np
from copy import deepcopy
import h5py
from tqdm import tqdm
from extra_geom import GenericGeometry
from extra_geom.base import DetectorGeometryBase
# Essiental
from SimExLite.utils.io import parseIndex
from SimExLite.PhotonBeamData import SimpleBeam, BeamBase
from SimExLite.DiffractionData import DiffractionData
import SimExLite


# Essential
def isFormat(fn: str):
    """Check if the data is in SimEx singfel diffraction HDF5 format"""
    try:
        with h5py.File(fn, 'r') as h5:
            if h5.keys() >= {"data", "info", "params"}:
                data_grp = h5['data']
                data_list = list(data_grp)
                if data_grp[data_list[0]].keys() >= {"data"}:
                    return True
                else:
                    return False
            else:
                return False
    except OSError:
        return False


# Essential
def getPatternTotal(filename):
    """Get the total number of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, 'r') as h5:
        npattern = len(h5['data'])
    return npattern


# Essential
def ireadPattern(filename, index=None, poissonize=True):
    """Iterator for reading diffraction patterns from a file."""
    index = parseIndex(index)
    pattern_type = getPatternType(poissonize)
    with h5py.File(filename, 'r') as h5:
        data_grp = h5['data']
        data_list = list(data_grp)
        data_list.sort()
        indices = data_list[index]

        for i in indices:
            yield data_grp[i][pattern_type][...], data_grp[i]['angle'][...]


# Essential
def read(filename, index=None, poissonize=True) -> DiffractionData:
    """Read diffraction patterns into an array from a file."""
    # Flush to print it before tqdm
    print('Reading singfelDiffr data...', flush=True)

    index = parseIndex(index)
    arr_size = len(range(getPatternTotal(filename))[index])
    pattern_shape = getPatternShape(filename)
    arr = np.zeros((arr_size, pattern_shape[0], pattern_shape[1]))
    quaternions = np.zeros((arr_size, 4))
    if isinstance(index, (slice, str)):
        with tqdm(total=arr_size) as progress_bar:
            for i, (pattern, quaternion) in enumerate(
                    ireadPattern(filename, index, poissonize)):
                arr[i] = pattern
                quaternions[i] = quaternion
                progress_bar.update(1)  # update progress
    else:
        # If only reading one pattern
        arr[0], quaternions[0] = next(ireadPattern(filename, index,
                                                   poissonize))

    params = getParameters(filename)
    geom, distance, pixel_mask = params2extra_geom(params['geom'])
    beam = params2SimpleBeam(params['beam'])

    DiffrData = DiffractionData(arr,
                                geom=geom,
                                beam=beam,
                                distance=distance,
                                quaternions=quaternions,
                                pixel_mask=pixel_mask)
    return DiffrData


# Essential
def write(filename,
          DiffrData: DiffractionData,
          method_desciption='',
          pmi_file_list=None):
    arr_counts = DiffrData.array
    quaternions = DiffrData.quaternions
    geom = extra_geom2params(DiffrData.geom, DiffrData.distance,
                             DiffrData.pixel_mask)
    beam = BeamData2params(DiffrData.beam)
    write_singfelDiffr(filename,
                       arr_counts=arr_counts,
                       geom=geom,
                       beam=beam,
                       quaternions=quaternions,
                       method_desciption=method_desciption,
                       pmi_file_list=pmi_file_list)


def write_singfelDiffr(filename,
                       arr_counts,
                       geom,
                       beam,
                       arr_intensity=None,
                       quaternions=None,
                       method_desciption='',
                       pmi_file_list=None):
    """
    Save pattern arrays as pysingfel diffraction data.

    :param filename: Output filename.
    :type filename: string
    :param arr_counts: The array of photon counting patterns after adding Poisson noise.
    :type arr_counts: `np.array`
    :param arr_intensity: The array of original diffraction patterns.
    :type arr_intensity: `np.array`
    :param quaternions: The list of the quaternion with which each diffraction pattern was generated.
    :type quaternions: list-like
    :param det: The dictionary of detector parameters.
    :type det: dict
    :param beam: The dictionary of beam parameters.
    :type beam: dict
    :param pmi_file_list: The list of the corresponding pmi output file of each diffraction pattern.
    :type pmi_file_list: list
    """
    prepH5(filename)
    # Method Description
    with h5py.File(filename, 'a') as f:
        f.create_dataset('info/method_description',
                         data=np.string_(method_desciption))
        # Flush to print it before tqdm
        print('Writing singfelDiffr data: data...', flush=True)
        for i, pattern_counts in enumerate(tqdm(arr_counts)):
            group_name = '/data/' + '{0:07}'.format(i + 1) + '/'
            f.create_dataset(group_name + 'data', data=pattern_counts)
            if (pmi_file_list is not None):
                # Link history from input pmi file into output diffr file
                group_name_history = group_name + 'history/parent/detail/'
                group_name_history = 'history/parent/detail/'
                f[group_name + '/history/parent/parent'] = h5py.ExternalLink(
                    pmi_file_list[i], 'history/parent')
                f[group_name_history + 'data'] = h5py.ExternalLink(
                    pmi_file_list[i], 'data')
                f[group_name_history + 'info'] = h5py.ExternalLink(
                    pmi_file_list[i], 'info')
                f[group_name_history + 'misc'] = h5py.ExternalLink(
                    pmi_file_list[i], 'misc')
                f[group_name_history + 'params'] = h5py.ExternalLink(
                    pmi_file_list[i], 'params')
                f[group_name_history + 'version'] = h5py.ExternalLink(
                    pmi_file_list[i], 'version')

        if arr_intensity is not None:
            print('Writing singfelDiffr data: diffr...', flush=True)
            for i, intensity in enumerate(tqdm(arr_intensity)):
                group_name = '/data/' + '{0:07}'.format(i + 1) + '/'
                f.create_dataset(group_name + 'diffr', data=intensity)

        if quaternions is not None:
            print('Writing singfelDiffr data: angle...', flush=True)
            for i, quaternion in enumerate(tqdm(quaternions)):
                group_name = '/data/' + '{0:07}'.format(i + 1) + '/'
                f.create_dataset(group_name + 'angle', data=quaternion)

        # Geometry
        f.create_dataset('params/geom/detectorDist', data=geom['detectorDist'])
        f.create_dataset('params/geom/pixelWidth', data=geom['pixelWidth'])
        f.create_dataset('params/geom/pixelHeight', data=geom['pixelHeight'])
        f.create_dataset('params/geom/mask', data=geom['mask'])

        # Beam
        f.create_dataset('params/beam/focusArea', data=beam['focusArea'])
        f.create_dataset('params/beam/photonEnergy', data=beam['photonEnergy'])


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


def getPatternShape(filename):
    """Get the shape of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, 'r') as h5:
        group_name = list(h5['data'])[0]
        try:
            return h5['data'][group_name]['diffr'].shape
        except KeyError:
            return h5['data'][group_name]['data'].shape


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


def params2extra_geom(file_geom):
    # The geometry dict from the file
    pixel_size = file_geom['pixelHeight']
    mask = file_geom['mask']
    center_pixel = (np.array(mask.shape)) / 2
    corner_coordinates = -center_pixel * pixel_size
    corner_coordinates = np.append(corner_coordinates, 0)
    simple_config = {
        'pixel_size': pixel_size,
        'slow_pixels': mask.shape[0],
        'fast_pixels': mask.shape[1],
        'corner_coordinates': [corner_coordinates],
        'ss_vec': np.array([0, 1, 0]),
        'fs_vec': np.array([1, 0, 0])
    }
    geom = GenericGeometry.from_simple_description(**simple_config)
    distance = file_geom['detectorDist']
    pixel_mask = deepcopy(file_geom['mask'])
    # In NeXus standard, bit 1 (value = 2) means dead.
    pixel_mask[file_geom['mask'] == 0] = 2
    pixel_mask[file_geom['mask'] == 1] = 0
    return geom, distance, pixel_mask


def params2SimpleBeam(file_beam):
    focus_area = file_beam['focusArea']
    photon_energy = file_beam['photonEnergy']
    beam = SimpleBeam(photon_energy=photon_energy, focus_area=focus_area)
    return beam


def extra_geom2params(geom: DetectorGeometryBase, distance, pixel_mask):
    if (geom.n_modules != 1):
        raise ValueError(
            "pysingfel can only deal with single-module geometry.")
    # extra_geom only deals with square pixel yet.
    pixel_size = geom.pixel_size
    mask = deepcopy(pixel_mask)
    # In pysingfel data, good_pixel = 1, bad_pixel = 0.
    mask[pixel_mask != 0] = 0
    mask[pixel_mask == 0] = 1
    geom_param = {
        'detectorDist': distance,
        'mask': mask,
        'pixelHeight': pixel_size,
        'pixelWidth': pixel_size
    }
    return geom_param


def BeamData2params(beam: BeamBase):
    focus_area = beam.get_focus_area().magnitude
    photon_energy = beam.get_photon_energy().magnitude
    beam_param = {'focusArea': focus_area, 'photonEnergy': photon_energy}
    return beam_param


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