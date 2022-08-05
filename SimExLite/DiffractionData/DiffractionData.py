# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

# Essiental
from tqdm import tqdm
from pathlib import Path
from importlib import import_module
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from SimExLite.PhotonBeamData import BeamBase
from SimExLite.utils.io import UnknownFileTypeError
import SimExLite.utils.analysis as utils
from extra_geom.detectors import DetectorGeometryBase
from pprint import pprint

###################### IO FORMATS LIST #######################################

# Initialize ioformats with UNKNOWN.
ioformats = {
    'UNKNOWN': {
        'desc': 'UNKNOWN data format',  # FORMAT_DISCRIPTION
        'ext': '',  # FORMAT_EXTENSION
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

ioformats['emc'] = {
    'desc': 'EMC Sparse Photon',
    'ext': 'emc',
    'module': 'SimExLite.DiffractionData.EMCPhoton',
    'kwargs': ['pattern_shape']
}

###################### IO FORMATS LIST END ###################################

def spliterate(buf, chunk):
    for start in range(0, len(buf), chunk):
        # print(start, start+chunk)
        yield buf[start:start + chunk]

def listFormats():
    """Print supported formats"""
    out_string = ''
    for key in ioformats:
        dicts = ioformats[key]
        out_string += f'Key: {key}\n'
        out_string += 'Description: {}\n'.format(dicts['desc'])
        ext = dicts['ext']
        if ext != '':
            out_string += 'File extension: {}\n'.format(ext)
        module = dicts['module']
        if module != '':
            out_string += 'API module: {}\n'.format(module)
        kwargs = dicts['kwargs']
        if kwargs != ['']:
            out_string += 'Extra reading keywords: {}\n'.format(kwargs)
        out_string += '\n'
    print(out_string)


def filetype(filename, kwargs=None) -> str:
    """Guess the type of the file"""
    fp = Path(filename)
    # Check if the path exists
    if not fp.exists():
        raise FileNotFoundError()

    format = 'UNKNOWN'
    # 1. Check if it is h5 file
    if fp.suffix.lower() == '.h5':
        ext = 'h5'
        format = filetype_content(filename)
        if format != 'UNKNOWN':
            return format

    # 2. If 1 failed, Check it with other extension
    for i in ioformats.keys():
        ext = ioformats[i]['ext']
        if fp.suffix.lower() == '.' + ext:
            format = i
            return format

    # 3. If 2 failed, check it with its content
    key = filetype_content(filename)
    if key != 'UNKNOWN':
        format = key
        return format

    # 4. check the extra keywords
    if format == 'UNKNOWN' and kwargs is not None:
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


class DiffractionData:
    """The diffraction data class

    :param arr: The input data array when you want to create a new diffraction data. [np,i,j]
    :type arr: `numpy.array`, optional
    :param geom: The diffraction geometry
    :type geom: extra_geom object, optional
    :param beam: The beam used for diffraction
    :type beam: :class:`BeamBase`, optional
    :param distance: Sample to detector distance (meter)
    :type distance: float
    :param pixel_mask: The 32-bit pixel mask for the detector. [np,i,j]
        https://manual.nexusformat.org/classes/applications/NXmx.html
        bit unset: perfect pixel; value = 0
        bit 0: gap (pixel with no sensor); value = 1
        bit 1: dead; value = 2
        bit 2: under-responding; value = 4
        bit 3: over-responding; value = 8
        bit 4: noisy; value = 16
        bit 5: -undefined-
        bit 6: pixel is part of a cluster of problematic pixels (bit set in addition to others); value = 64
        bit 7: -undefined-
        bit 8: user defined mask (e.g. around beamstop); value = 256
        bits 9-30: -undefined-
        bit 31: virtual pixel (corner pixel with interpolated value); value = 2147483648
    :type pixel_mask: 2D numpy.uint32 ndarray
    """
    def __init__(self,
                 arrary: ndarray = None,
                 geom: DetectorGeometryBase = None,
                 beam: BeamBase = None,
                 distance: float = None,
                 quaternions: ndarray = None,
                 pixel_mask: ndarray = None) -> None:
        super().__init__()

        self.__array = arrary
        self.geom = geom
        self.beam = beam
        self.distance = distance
        self.pixel_mask = pixel_mask
        self.quaternions = quaternions
        self.__statistic_to_update = True

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

    def multiply(self, val, chunk_size=10000):
        """Multiply a number to the diffraction patterns.

        :param val: The value to be multiplied.
        :type val: float
        :param chunk: The chunk size to conduct the operation
        :type chunk_size: int
        """
        for arr in tqdm(spliterate(self.array, chunk_size),total=int(np.ceil(float(len(self.array))/chunk_size))):
            arr[:] = arr * val
        self.__statistic_to_update = True

    def setArrayDataType(self, data_type):
        """The the data numpy array dtype

        :param data_type: The numpy dtype to be set. E.g. 'int32'
        :type data_type: `numpy.dtype`
        """
        self.__array = self.array.astype(data_type)
        self.__statistic_to_update = True

    def writeGeometry(self, file_name: str):
        """Write the detector geometry in crystFEL geometry file

        :param file_name: The name of the output geometry file.
        :type file_name: str
        """
        file_path = Path(file_name)
        geom_path = file_path.with_suffix('.geom')
        fn_geom = str(geom_path)
        print('writing .geom to {}'.format(fn_geom))
        self.geom.write_crystfel_geom(
            fn_geom,
            dims=('frame', 'ss', 'fs'),
            adu_per_ev=1.0,
            clen=self.distance,
            photon_energy=self.beam.get_photon_energy().magnitude,
            nquads=1,
            data_path='/data/data',
        )

    def writeEmcIni(self, file_name=None):
        if file_name:
            conf_path = file_name
        else:
            conf_path = 'config.ini'
        config_ini = """# Generated by SimEx
[parameters]
detd = {}
lambda = {}
detsize = {} {}
pixsize = {}
stoprad = {}
polarization = x

[emc]
#in_photons_file = 
#in_detector_file = 
#num_div = 6 9 12 15 19 24
output_folder = ./
log_file = EMC.log""".format(self.distance * 1e3, self.beam.wavelength,
                             self.geom.frag_ss_pixels,
                             self.geom.frag_fs_pixels,
                             self.geom.pixel_size * 1e3, self.stop_rad)
        with open(str(conf_path), 'w') as f:
            f.write(config_ini)

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
        return self.__array

    @array.setter
    def array(self, val):
        """Set the value of array"""
        self.__array = val
        self.__statistic_to_update = True

    @property
    def stop_rad(self):
        """Beamstop radius in pixel"""
        try:
            return self.__stop_rad
        except AttributeError:
            self.__stop_rad = 0
            return self.__stop_rad

    @property
    def pattern_total(self) -> int:
        """The total number of the diffraction patterns read into this class"""
        return len(self.array)


def read(filename: str,
         index=None,
         format: str = None,
         **kwargs) -> DiffractionData:
    """Read a DiffractionData object from file.

    :param filename: Name of the file to read with.
    :type filename: str
    :param index: All the snapshots will be read by default.  Examples:
        * ``index=None``: read all the snapshots
        * ``index=0``: first snapshot
        * ``index=-2``: second to last
        * ``index=':'`` or ``index=slice(None)``: all
        * ``index='-3:'`` or ``index=slice(-3, None)``: three last
        * ``index='::2'`` or ``index=slice(0, None, 2)``: even
        * ``index='1::2'`` or ``index=slice(1, None, 2)``: odd
    :type index: int, slice or str
    :param format: The format key to specify the file-format.  If not given, the function will
        guess the file-format. `listFormats()` to list supported formats.
    :type format: str

    :return: Diffraction data class instance
    :rtype: :class:`SimEx.DiffractionData.DiffractionData`
    """
    if format is None:
        format = filetype(filename)
    try:
        module_name = ioformats[format]['module']
    except KeyError:
        raise UnknownFileTypeError(f"Unsupported format {format}.")

    data_module = import_module(module_name)
    __read = data_module.read
    DiffrData = __read(filename, index, **kwargs)
    return DiffrData


def write(filename: str, object: DiffractionData, format: str,
          **kwargs) -> None:
    """Read a DiffractionData object from file.

    :param filename: Name of the file to save with.
    :type filename: str
    :param object: The object of DiffractionData class to save.
    :type object: :class:`SimEx.DiffractionData.DiffractionData`
    :param format: The format key to specify the file-format. Supported format keys
    can be checked with `listFormats()`
    :type format: str
    """
    try:
        module_name = ioformats[format]['module']
    except KeyError:
        raise UnknownFileTypeError(f"Unsupported format: '{format}'.")
    data_module = import_module(module_name)
    __write = data_module.write
    __write(filename, object, **kwargs)


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
            'Warnning: zero-value detected. Please set a small offset (e.g. 1e-3) to get correct log display.'
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
