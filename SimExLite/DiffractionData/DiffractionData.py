# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

from tqdm import tqdm
from pathlib import Path
from importlib import import_module
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from SimExLite.PhotonBeamData import BeamBase
from SimExLite.utils.io import UnknownFileTypeError
from extra_geom.detectors import DetectorGeometryBase


###################### IO FORMATS LIST #######################################

# Initialize ioformats with UNKNOWN.
ioformats = {
    'UNKNOWN': {
        'desc': 'UNKNOWN data format',  # FORMAT_DISCRIPTION
        'ext': 'unknown',  # FORMAT_EXTENSION
        'module': '',  # MODULE_NAME
        'kwargs': ['']  # KEYWORDS_LIST
    }
}

# Each IO format can have extra keywords,
# such as ['poissonize'], which defines if some of the formats will read the poissonized patterns.
ioformats['singfel'] = {
    'desc': 'SIMEX SingFEL',
    'ext': 'h5',
    'module': 'SimExLite.DiffractionData.singfelDiffr',
    'kwargs': ['poissonize']
}

# ioformats['emc'] = {
#     'desc': 'EMC Sparse Photon',
#     'ext': 'emc',
#     'module': 'SimExLite.DiffractionData.EMCPhoton',
#     'kwargs': ['pattern_shape']
# }

###################### IO FORMATS LIST END ###################################


def filetype(filename, kwargs=None) -> str:
    """Guess the type of the file"""
    fp = Path(filename)
    format = 'UNKNOWN'

    ext = 'unknown'
    # 1. Check if it is h5 file
    if fp.suffix.lower() == '.h5':
        ext = 'h5'
        format = filetype_content(filename)
        if format != 'UNKNOWN':
            return format

    # 2. If 1 failed, Check it with other extension
    if ext == 'unknown':
        for i in ioformats.keys():
            ext = ioformats[i]['ext']
            if fp.suffix.lower() == '.' + ext:
                format = i
                return format

    # 3. If 2 failed, check it with its content
    if ext == 'unknown':
        for i in ioformats.keys():
            format = filetype_content(filename)
            if format != 'UNKNOWN':
                ext = ioformats[i]['ext']
                return format

    # 4. check the extra keywords
    if ext == 'unkown' and kwargs is not None:
        format = filetype_keywords(kwargs)

    if format == 'UNKNOWN':
        raise UnknownFileTypeError('Could not guess file type')

    return format

def filetype_content(filename) -> str:
    """Guess the type of a file by its content"""

    for i in ioformats.keys():
        module_name = ioformats[i]['module']
        if module_name == '':
            continue
        data_module = import_module(module_name)
        if data_module.isFormat(filename):
            return i
    return 'UNKNOWN'

def filetype_keywords(kwargs) -> str:
    """Guess the type from the input keywords"""
    for kw in kwargs.keys():
        for i in ioformats.keys():
            kws = ioformats[i]['kwargs']
            if kw in kws:
                return i
    # When there is no match, return UNKNOWN.
    return 'UNKNOWN'

def read(filename: str, index = None, format: str = None, **kwargs):
    """Read a DiffractionData object from file.

    :param filename: Name of the file to read.
    :type filename: str or file
    :param index: All the snapshots will be read by default.  Examples:
        * ``index=None``: read all the snapshots
        * ``index=0``: first snapshot
        * ``index=-2``: second to last
        * ``index=':'`` or ``index=slice(None)``: all
        * ``index='-3:'`` or ``index=slice(-3, None)``: three last
        * ``index='::2'`` or ``index=slice(0, None, 2)``: even
        * ``index='1::2'`` or ``index=slice(1, None, 2)``: odd
    :type index: int, slice or str
    :param format: Used to specify the file-format.  If not given, the
        file-format will be guessed by the *getFileType* function.
    :type format: str

    :return: Diffraction data class instance
    :rtype: :class:`DiffractionData`
    """
    if format is None:
        format = filetype(filename)
    module_name = ioformats[format]['module']
    data_module = import_module(module_name)
    __read = data_module.read
    arr = __read(filename=filename, index=index, **kwargs)

def createDiffractionData(arr: np.array = None,
                          geometry: DetectorGeometryBase = None,
                          beam: BeamBase = None):
    """Create a DiffractionData class from existed array.

    :param arr: The input data array when you want to create a new diffraction data
    :type arr: `np.numpy`
    :param geometry: The diffraction geometry
    :type geometry: dict or extra_geom geometry
    :param beam: The beam used for diffraction
    :type beam: :class:`BeamBase`

    :return: Diffraction data class instance
    :rtype: :class:`DiffractionData`
    """
    DD = DiffractionData(arr=arr, geometry=geometry, beam=beam)
    return DD


class DiffractionData:
    """The diffraction data class

    :param arr: The input data array when you want to create a new diffraction data
    :type arr: `np.numpy`, optional
    :param geometry: The diffraction geometry
    :type geometry: dict or extra_geom geometry, optional
    :param beam: The beam used for diffraction
    :type beam: :class:`BeamBase`, optional
    """
    def __init__(self,
                 arr: np.array = None,
                 geometry: DetectorGeometryBase = None,
                 beam: BeamBase = None) -> None:
        super().__init__()

        if arr is not None:
            # Writting mode
            self.__array = arr
            self.__statistic_to_update = True
        # Writting mode
        if geometry is not None:
            self.__geometry = geometry
        if beam is not None:
            self.__beam = beam
        # Beam stop radius in pixel
        self.__stop_rad = 0

    # This is the essential part of this class
    def _createArray(self):
        """Create a numpy array from the input diffraction data defined by :func:`read`.
            The array can be accessed by :attr:`DiffractionData.array`.
        """
        data = self.__backengine
        data.createArray(self.index_range, self.poissonize)
        self.__array = data.array
        self.__statistic_to_update = True

        if len(self.__array.shape) == 2:
            self.__array = np.expand_dims(self.__array, axis=0)
        elif len(self.__array.shape) < 2:
            raise ValueError("Array dimension should >= 2")

    def addBeamStop(self, stop_rad: int):
        """Add a beamstop in pixel radius to the diffraction patterns.

        :param stop_rad: The radius of the beamstop in pixel unit
        :type stop_rad: int
        """
        array = self.array
        print("Adding beam stop...", flush=True)
        for i, img in enumerate(tqdm(array)):
            array[i] = addBeamStop(img, stop_rad)
        self.__stop_rad = stop_rad
        self.__statistic_to_update = True

    def addGaussianNoise(self, mu, sigs_popt):
        """Add Gaussian noise to one diffraction pattern.

        :param mu: The average ADU for one photon
        :type mu: float

        :param sigs_popt: A list of [slop, intercept]
        :type sigs_popt: list-like
        """
        array = self.array
        print("Adding Gaussian Noise...", flush=True)
        for i, diffr_data in enumerate(tqdm(array)):
            array[i] = addGaussianNoise(diffr_data, mu, sigs_popt)
        self.__statistic_to_update = True

    def multiply(self, val):
        """Multiply a number to the diffraction patterns.

        :param val: The value to be multiplied.
        :type val: float
        """
        self.__array = self.array * val
        self.__statistic_to_update = True

    def setArrayDataType(self, data_type):
        """The the data numpy array dtype

        :param data_type: The numpy dtype to be set. E.g. 'int32'
        :type data_type: `numpy.dtype`
        """
        self.__array = self.array.astype(data_type)
        self.__statistic_to_update = True

    def writeGeometry(self, data_format: str, file_name: str):
        file_path = Path(file_name)
        if data_format == "emc":
            geom_path = file_path.with_suffix('.geom')
            fn_geom = str(geom_path)
            print('writing .geom to {}'.format(fn_geom))
            self.geometry.write_crystfel_geom(
                fn_geom,
                dims=('frame', 'ss', 'fs'),
                adu_per_ev=1.0,
                clen=self.geometry.clen,
                photon_energy=self.beam.photon_energy.to('eV').magnitude,
                nquads=1,
                data_path='/data/data',
            )

            conf_path = file_path.parent / 'config.ini'
            config_ini = """# Generated by SimEx
[parameters]
detd = {}
lambda = {}
detsize = {} {}
pixsize = {}
stoprad = {}
polarization = x

[emc]
output_folder = ./
log_file = EMC.log""".format(self.geometry.clen * 1e3,
                             self.beam.wavelength.to('angstrom').magnitude,
                             self.geometry.frag_ss_pixels,
                             self.geometry.frag_fs_pixels,
                             self.geometry.pixel_size * 1e3, self.stop_rad)
            with open(str(conf_path), 'w') as f:
                f.write(config_ini)

    def saveAs(self, data_format: str, file_name: str, with_geom=None):
        """Save the diffraction data as a specific data_format.

        :param data_format: The data format key representing the saving data format:

                ==========  ===========
                Format key  Description
                ==========  ===========
                simple      A simple data array in HDF5
                singfel     SIMEX SingFEL
                emc         EMC Sparse Photon
                ==========  ===========

        :type data_format: str
        :param file_name: The file name of the new data
        :type file_name: str
        :param with_geom: whether to save geometry information, defaults to `None` to let the program decide itself.
        :type with_geom: bool, optional
        """
        array_to_save = self.array

        if data_format == "emc":
            file_path = Path(file_name)
            # Add '.emc' suffix if no suffix specified
            file_path.with_suffix('.emc')
            fn_data = str(file_path)
            arr2emc(array_to_save, fn_data)

            if with_geom:
                self.writeGeometry(data_format, file_name)

        elif data_format == "simple":
            utils.saveSimpleH5(array_to_save, file_name)
        else:
            raise TypeError("Unsupported format: ".format(data_format))

    def plotPattern(self,
                    idx: int,
                    logscale=True,
                    offset=None,
                    symlog=False,
                    fn_png=None,
                    *argv,
                    **kwargs):
        """ Plot a pattern.

        :param idx: The array index of the pattern to plot (starting from 0)
        :type idx: idx
        :param logscale: Whether to show the data on logarithmic scale (z axis), defaults to `True`.
        :type logscale: bool, optional
        :param offset: Offset to apply to the pattern.
        :type offset: float, optional
        :param symlog: To show the data on symlogarithmic scale (z axis), default to `False`.
        :type symlog: bool, optional
        :param fn_png: The name of the output png file, defaults to `None`.
        :type fn_png: str, optional

        :return: The axes class instance of the plot.
        :rtype: ``matplotlib.axes``
        """
        array_to_plot = self.array[idx]
        plotImage(array_to_plot,
                  logscale=logscale,
                  offset=offset,
                  symlog=symlog,
                  fn_png=fn_png,
                  *argv,
                  **kwargs)

    def __setStatistics(self):
        """Get photon statistics"""

        patterns = self.array

        pattern_total = len(patterns)
        pattern_dim = patterns[0].shape
        pixel_num = pattern_dim[0] * pattern_dim[1]
        # Number of pixels with zero photons
        avg_zero_pixel_num = (
            patterns.size - np.count_nonzero(patterns)) / pattern_total
        # Sum the photons in each pattern
        photons = np.sum(patterns, axis=(1, 2))
        # Average photon number over all the patterns
        avg_photons = np.mean(photons)
        # Maximum photon number over all the patterns
        max_photons = np.max(photons)
        # Min photon number over all the patterns
        min_photons = np.min(photons)
        # Average photons per pixel in each pattern
        avg_per_pattern = photons / pixel_num
        # Average number of photons of a pixel
        avg_avg_per_pattern = np.mean(avg_per_pattern)
        # Maximum photons in each pattern
        max_per_pattern = np.max(patterns, axis=(1, 2))
        # Average maximum photon number in a pixel over all the patterns
        avg_max_per_pattern = np.mean(max_per_pattern)
        # Minimum photons in each pattern
        min_per_pattern = np.min(patterns, axis=(1, 2))
        # Average minimum photon number in a pixel over all the patterns
        avg_min_per_pattern = np.mean(min_per_pattern)

        statistics = {
            'Number of patterns':
            pattern_total,
            'Average number of photons of a pattern':
            avg_photons,
            'Maximum number of photons of a pattern':
            max_photons,
            'Minimum number of photons of a pattern':
            min_photons,
            'STD of total number of photons of a pattern':
            np.std(photons),
            'Average number of zero-photon pixels':
            avg_zero_pixel_num,
            'Average percentage of zero-photon pixels':
            avg_zero_pixel_num / patterns[0].size,
            'Average number of photons of a pixel':
            avg_avg_per_pattern,
            'Maximum number of photons of a pixel averaging over the patterns':
            avg_max_per_pattern,
            'Minimum number of photons of a pixel averaging over the patterns':
            avg_min_per_pattern,
        }

        self.__photon_totals = photons
        self.__photon_statistics = statistics
        self.__statistic_to_update = False

    def plotHistogram(self, fn_png=None):
        pattern_total = self.photon_statistics['Number of patterns']
        max_photons = self.photon_statistics[
            'Maximum number of photons of a pattern']
        min_photons = self.photon_statistics[
            'Minimum number of photons of a pattern']
        number_of_bins = min(20, pattern_total)
        binwidth = (max_photons - min_photons) / number_of_bins
        try:
            plt.hist(self.photon_totals,
                     bins=np.arange(min_photons, max_photons, binwidth),
                     facecolor='red',
                     alpha=0.75)
        except ValueError as e:
            if 'cannot compute length' in str(e):
                raise ValueError(
                    'Please load more than one diffraction pattern.')
            else:
                raise e
        plt.xlabel("Photons")
        plt.ylabel("Histogram")
        plt.title("Photon number histogram")
        if fn_png is None:
            plt.show()
        else:
            plt.savefig(fn_png, dpi=300)

    @property
    def input_file_type(self) -> str:
        """Return a string describing the input file type"""
        return format_id_dict[self.format_id]

    @property
    def photon_statistics(self) -> dict:
        """The photon statistics of the patterns"""
        if self.__statistic_to_update is True:
            self.__setStatistics()
            return self.__photon_statistics
        else:
            return self.__photon_statistics

    @property
    def photon_totals(self) -> np.array:
        """The total photons of the patterns"""
        if self.__statistic_to_update is True:
            self.__setStatistics()
            return self.__photon_totals
        else:
            return self.__photon_totals

    @property
    def array(self):
        """The numpy array of the diffraction patterns"""
        try:
            return self.__array
        except AttributeError:
            # raise AttributeError(
            #     "Please use DiffractionData.createArray() to get the array ready first."
            # )
            self._createArray()

    @array.setter
    def array(self, val):
        """Set the value of array"""
        self.__array = val
        self.__statistic_to_update = True

    @property
    def stop_rad(self):
        """Beamstop radius in pixel"""
        return self.__stop_rad

    @property
    def pattern_total(self) -> int:
        """The total number of the diffraction patterns read into this class"""
        try:
            return len(self.array)
        except AttributeError:
            n = 0
            for ix in self.iterator:
                n += 1
            return n

    @property
    def geometry(self):
        """Return the geometry parameters"""
        try:
            return self.__geometry
        except AttributeError:
            format_id = self.format_id
            if format_id == '1':
                return getSingfelDiffrGeom(self.input_file)
            else:
                raise TypeError("UNKNOWN file type")

    @property
    def beam(self):
        """Return the beam parameters"""
        try:
            return self.__beam
        except AttributeError:
            format_id = self.format_id
            if format_id == '1':
                return getSingfelDiffrBeam(self.input_file)
            else:
                raise TypeError("UNKNOWN file type")


def getFileType(fn) -> str:
    # Is hdf5?
    if h5py.is_hdf5(fn):
        if (isLegacySimExH5(fn)):
            with h5py.File(fn, 'r') as h5:
                idx = list(h5['data'].keys())[0]
                # If the h5 file has these keys
                if h5['data'][idx].keys() >= {'angle', 'data', 'diffr'}:
                    # SIMEX SingFEL
                    return "1"
                else:
                    print("This input file: {} contains no diffraction data".
                          format(fn))
                    return "0"
        elif (isEMCH5(fn)):
            return "2"
        else:
            # UNKOWN HDF5
            return "4"
    else:
        if isEMCBinary(fn):
            return "2"
        # UNKOWN DATA
        return "0"


def addBeamStop(img, stop_rad):
    """Add the beamstop in pixel radius to diffraction pattern.

    :param img: Diffraction pattern
    :type img: np.2darray
    :param stop_rad: The radius of the beamstop in pixel unit
    :type stop_rad: int

    :return: Beamstop masked 2D array
    :rtype: np.2darray
    """
    stop_mask = np.ones_like(img)
    center = np.array(img.shape) // 2
    y = np.indices(img.shape)[0] - center[0]
    x = np.indices(img.shape)[1] - center[1]
    r = np.sqrt((x * x + y * y))
    stop_mask[r <= stop_rad] = 0
    masked = img * stop_mask
    return masked


def getPatternStatistics(img):
    """Get photon statistic info of a pattern.

    :param img: Diffraction pattern
    :type img: np.2darray

    :return: A tuple of (mean, max, min)
    :rtype: tuple
    """
    img_flat = img.ravel()
    mean_val = img_flat.mean()
    max_val = img_flat.max()
    min_val = img_flat.min()

    statistics = {'mean': mean_val, 'min': min_val, 'max': max_val}

    return statistics


def addGaussianNoise(diffr_data, mu, sigs_popt):
    """Add Gaussian noise to one diffraction pattern.

    :param diffr_data: A diffraction pattern
    :type diffr_data: `numpy.array`
    :param mu: The averange ADU for one photon
    :type mu: float
    :param sigs_popt: A list of [slop, intercept]
    :type sigs_popt: list-like
    """
    sig_arr = utils.linear(diffr_data, *sigs_popt)
    diffr_noise = np.random.normal(diffr_data * mu, sig_arr)
    return diffr_noise


def getSingfelDiffrGeom(fn: str) -> DetectorGeometryBase:
    params = getParameters(fn)
    pn = params['geom']['mask'].shape
    x_pixel_size = params['geom']['pixelWidth']
    y_pixel_size = params['geom']['pixelHeight']
    if x_pixel_size != y_pixel_size:
        raise ValueError("Pixel width and height should be the same.")
    pixel_size = x_pixel_size
    # Horizontal (x) direction
    fs_vec = np.array([1, 0, 0]) * pixel_size
    fs_pixels = pn[1]
    cnx = -fs_pixels * 0.5
    # Vertical (y) direction
    ss_vec = np.array([0, 1, 0]) * pixel_size
    ss_pixels = pn[0]
    cny = -ss_pixels * 0.5
    # Sample to detector distance
    clen = params['geom']['detectorDist']
    coffset = 0
    corner_pos = np.array([cnx * pixel_size, cny * pixel_size, coffset])
    frag = GeometryFragment(corner_pos, ss_vec, fs_vec, ss_pixels, fs_pixels)
    modules = [[frag]]
    detector = simpleGeometry(modules,
                              pixel_size=pixel_size,
                              ss_pixels=ss_pixels,
                              fs_pixels=fs_pixels)
    detector.clen = clen  # meter
    return detector


def getSingfelDiffrBeam(fn: str) -> BeamBase:
    params = getParameters(fn)
    photon_energy = params['beam']['photonEnergy']  # eV
    beam = BeamBase(photon_energy=photon_energy)
    return beam


class simpleGeometry(DetectorGeometryBase):
    """A simple geometry based on extra_geom DetectorGeometryBase.

    :param pixel_size: Pixel size in meter
    :type pixel_size: float
    :param ss_pixel: Number of slow scan pixels, it's usually y-direction
     pixels in simple geometry
    :type ss_pixel: int
    :param fs_pixel: Number of fast scan pixels, it's usually x-direction
     pixels in simple geometry
    :type fs_pixel: int
    """
    def __init__(self,
                 modules=None,
                 filename='Simple Geom',
                 pixel_size=None,
                 ss_pixels=None,
                 fs_pixels=None,
                 clen=None):
        super().__init__(modules, filename=filename)
        self.detector_type_name = 'Simple'
        self.pixel_size = pixel_size  # in metre
        self.frag_ss_pixels = ss_pixels
        self.frag_fs_pixels = fs_pixels
        self.clen = clen
        self.expected_data_shape = (1, ss_pixels, fs_pixels)
        self.n_quads = 1
        self.n_tiles_per_module = 1
        self.n_modules = 1

    def _tile_slice(self, tileno):
        # Which part of the array this tile is.
        ss_slice = slice(0, self.frag_ss_pixels)
        fs_slice = slice(0, self.frag_fs_pixels)
        return ss_slice, fs_slice


class histogramParams:
    """Fitting results of a detector histogram.

    :param xcs: Gaussian peak centers
    :type xcs: `numpy.array`
    :param fwhms: FWHMs for the peaks
    :type fwhms: `numpy.array`
    :param sigs: Sigmas for the peaks
    :type sigs: `numpy.array`, optional
    """
    def __init__(self, xcs, fwhms=None, sigs=None):
        if fwhms is not None and sigs is None:
            self.fwhm = fwhms
            self.sigs = fwhms / 2.355
        elif fwhms is None and sigs is not None:
            self.sigs = sigs
            self.fwhm = sigs * 2.355
        else:
            raise ValueError("Don't input fwhms and sigs at the same time.")

        fitting = getSigsFitting(self.sigs)

        # ADU/photon
        self.mu = np.mean(np.diff(xcs))
        self.sigs_popt = fitting.popt
        self.fitting = fitting

    def plotFitting(self, fn_png="fitting.png"):
        """Plot the fitting results to a .png file, default: fitting.png"""
        self.fitting.plotResults(xlabel='photons', ylabel='sigma', fn=fn_png)


def arr2emc(array_to_save: np.array, fn_data: str):
    print('writing {} to {}'.format(array_to_save.shape, fn_data), flush=True)
    emcwriter = writeemc.EMCWriter(
        fn_data, array_to_save[0].shape[0] * array_to_save[0].shape[1])
    for photons in tqdm(array_to_save):
        emcwriter.write_frame(photons.astype(np.int32).ravel())


def getSigsFitting(sigs):
    """Get the fitting parameters for predicting sigmas"""
    xdata = np.arange(len(sigs))
    ydata = sigs
    my_fitting = utils.curve_fitting(utils.linear, xdata, ydata)
    return my_fitting


def plotImage(pattern,
              logscale=True,
              offset=None,
              symlog=False,
              figsize=None,
              ax=None,
              fn_png=None,
              *argv,
              **kwargs):
    """ Workhorse function to plot an image.

    :param logscale: Whether to show the data on logarithmic scale (z axis), defaults to `True`.
    :type logscale: bool
    :param offset: Offset to apply to the pattern.
    :type offset: float
    :param symlog: To show the data on symlogarithmic scale (z axis), defaults to `False`.
    :type symlog: bool
    :param fn_png: The name of the output png file, defaults to `None`.
    :type fn_png: str

    :return: The axes class instance of the plot.
    :rtype: ``matplotlib.axes``
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    # Get limits.
    mn, mx = pattern.min(), pattern.max()

    x_range, y_range = pattern.shape

    if offset:
        mn = pattern.min() + offset
        mx = pattern.max() + offset
        pattern = pattern.astype(float) + offset

    if (logscale and symlog):
        print('logscale and symlog are both true.\noverrided by logscale')

    if 0 in pattern and not offset and (logscale or symlog):
        print(
            'Warnning: zero-value detected. Setting a small offset to get correct log display.'
        )

    if (logscale or symlog):
        kwargs['cmap'] = kwargs.pop('cmap', "viridis")
        # default plot setup
        if logscale:
            kwargs['norm'] = kwargs.pop('norm', colors.LogNorm())
        elif symlog:
            kwargs['norm'] = kwargs.pop('norm', colors.SymLogNorm(0.015))
        kwargs.pop('axes', None)
    else:
        kwargs['norm'] = kwargs.pop('norm', colors.Normalize(vmin=mn, vmax=mx))
        kwargs['cmap'] = kwargs.pop('cmap', "viridis")
    ax = plt.imshow(pattern, *argv, **kwargs)

    plt.xlabel(r'$x$ (pixel)')
    plt.ylabel(r'$y$ (pixel)')
    plt.xlim([0, x_range - 1])
    plt.ylim([0, y_range - 1])
    plt.tight_layout()
    plt.colorbar()
    if fn_png:
        plt.savefig(fn_png, dpi=300)
    return ax
