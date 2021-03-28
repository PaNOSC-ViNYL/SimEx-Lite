# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

from tqdm import tqdm
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from SimExLite.utils import isLegacySimExH5
from SimExLite.DataAPI.singfelDiffr import singfelDiffr
import SimExLite.DataAPI.EMCPhoton as EMC
import SimExLite.utils as utils

data_type_dict = {
    '0': 'UNKOWN',
    '1': 'SIMEX SingFEL',
    '2': 'EMC Sparse Photon',
    '3': 'NeXus',
    '4': 'UNKOWN HDF5'
}


class DiffractionData:
    """The diffraction data class

    :param input_file: The data file name to read
    :type input_file: str
    :param keep_original: If keep the original data array, defaults to `True`. If set to
    `False`, all the changes will apply to func:`DiffractionData.array`.
    It's recommended to set it to `False` when the array is large.
    :type keep_original: bool, optional
    :param arr: The input data array when you want to create a new diffraction data
    :type arr: `np.numpy`, optional
    :param parameters: The input diffraction parameter dictionary when you want to
    create a new diffraction data
    :type parameters: dict
    """
    def __init__(self,
                 input_file: str = None,
                 keep_original=True,
                 arr: np.array = None,
                 parameters=None) -> None:
        super().__init__()
        self.keep_original = keep_original

        if arr is None and input_file is None:
            raise ValueError("Need least one `arr` or `input_file`")

        if arr is not None:
            # Writting mode
            self.__array = arr
        else:
            # Reading mode
            self.input_file = input_file
            # Check if the file exists
            with open(self.input_file, 'r') as f:
                f.close()
            self.type_id_read = getDataType(self.input_file)
        if parameters is not None:
            self.parameters = parameters

    def getArray(self, index_range=None):
        """Get a numpy array of the diffraction data

        :param index_range: The indices of the diffraction patterns to dump to the numpy array,
        defaults to `None` meaning to take all the patterns. The array can be accessed by
        func:`DiffractionData.array`.
        :type index_range: list-like or `int`, optional
        """
        type_id_read = self.type_id_read
        if type_id_read == '0':
            raise TypeError("UNKNOWN data format.")
        elif type_id_read == '1':
            data = singfelDiffr(self.input_file)
            data.getArray(index_range)
            self.__array = data.array

    def addBeamStop(self, stop_rad: int):
        """Add the beamstop in pixel radius to the diffraction patterns

        :param stop_rad: The radius of the beamstop in pixel unit
        :type stop_rad: int
        """
        processed = self.processed
        print("Adding beam stop...")
        for i, img in enumerate(tqdm(processed)):
            processed[i] = addBeamStop(img, stop_rad)

    def saveAs(self, data_format: str, file_name: str, save_original=False):
        """Save the diffraction data as a specific data_format

        :param data_format: The data format to save in.
        Supported formats:
            simple: A simple data array in hdf5
            singfel: SIMEX SingFEL
            emc: EMC Sparse Photon
        :type data_format: str
        :param file_name: The file name of the new data
        :type file_name: str
        :param save_original: If it's true, will save the original array, instead of the processed
        one; defaults to False to save the processed array.
        :type save_original: bool
        """
        if save_original:
            array_to_save = self.array
        else:
            array_to_save = self.processed

        if data_format == "emc":
            print('writing {} to {}'.format(array_to_save.shape, file_name))
            data = []
            for img in tqdm(array_to_save):
                data.append(img.flatten())
            data = np.array(data)
            patterns = EMC.dense_to_PatternsSOne(data)
            patterns.write(file_name)
        elif data_format == "simple":
            utils.saveSimpleH5(array_to_save, file_name)
        else:
            raise TypeError("Unsupported format: ".format(data_format))

    def addGaussianNoise(self, mu, sigs_popt):
        """Add Gaussian noise to one diffraction pattern

        :param mu: The averange ADU for one photon
        :type mu: float

        :param sigs_popt: [slop, intercept]
        :type sigs_popt: list-like
        """
        processed = self.processed
        print("Adding Gaussian Noise...")
        for i, diffr_data in enumerate(tqdm(processed)):
            processed[i] = addGaussianNoise(diffr_data, mu, sigs_popt)

    def plotPattern(self,
                    idx: int,
                    logscale=False,
                    offset=None,
                    symlog=False,
                    original=False,
                    fn_png=None,
                    *argv,
                    **kwargs):
        """ Plot a pattern.

        :param idx: The array index of the pattern to plot (starting from 0)
        :type idx: idx
        :param logscale: Whether to show the data on logarithmic scale (z axis) (default False).
        :type logscale: bool
        :param offset: Offset to apply to the pattern.
        :type offset: float
        :param symlog: To show the data on symlogarithmic scale (z axis) (default False).
        :type symlog: bool
        :param original: Whether to plot the original or processed pattern, defauts to `False` for processed
        pattern.
        :type original: bool
        :param fn_png: The name of the output png file, defaults to `None`.
        :type fn_png: str
        """
        if original:
            array_to_plot = self.array[idx]
        else:
            array_to_plot = self.processed[idx]
        plotImage(array_to_plot,
                  logscale=logscale,
                  offset=offset,
                  symlog=symlog,
                  fn_png=fn_png,
                  *argv,
                  **kwargs)

    @property
    def array(self):
        """The original pattern array"""
        try:
            return self.__array
        except AttributeError:
            raise AttributeError(
                "Please use DiffractionData.getArray() to get the array ready first."
            )

    @property
    def processed(self):
        """The processed pattern array"""
        try:
            if self.keep_original:
                return self.__processed
            else:
                return self.array
        except AttributeError:
            # Initialize the processed array
            self.__processed = np.copy(self.array)
            return self.__processed


def getDataType(fn) -> str:
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
        else:
            # UNKOWN HDF5
            return "4"
    else:
        # UNKOWN DATA
        return "0"


def addBeamStop(img, stop_rad):
    """Add the beamstop in pixel radius to diffraction pattern

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


def getPatternStatistic(img):
    """Get photon statistic info of a pattern

    :param img: Diffraction pattern
    :type img: np.2darray

    :return: (mean, max, min)
    :rtype: tuple
    """
    img_flat = img.ravel()
    mean_val = img_flat.mean()
    max_val = img_flat.max()
    min_val = img_flat.min()
    print('Mean: {}'.format(mean_val))
    print('Max: {}'.format(max_val))
    print('Min: {}'.format(min_val))

    return (mean_val, max_val, min_val)


def addGaussianNoise(diffr_data, mu, sigs_popt):
    """Add Gaussian noise to one diffraction pattern

    :param diffr_data: A diffraction pattern
    :type diffr_data: `numpy.array`
    :param mu: The averange ADU for one photon
    :type mu: float
    :param sigs_popt: [slop, intercept]
    :type sigs_popt: list-like
    """
    sig_arr = utils.linear(diffr_data, *sigs_popt)
    diffr_noise = np.random.normal(diffr_data * mu, sig_arr)
    return diffr_noise


class histogramParams:
    """Fitting results of a detector histogram

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
    """Get the fitting parametters for predicting sigmas"""
    xdata = np.arange(len(sigs))
    ydata = sigs
    my_fitting = utils.curve_fitting(utils.linear, xdata, ydata)
    return my_fitting


def plotImage(pattern,
              logscale=False,
              offset=None,
              symlog=False,
              fn_png=None,
              *argv,
              **kwargs):
    """ Workhorse function to plot an image

    :param logscale: Whether to show the data on logarithmic scale (z axis) (default False).
    :type logscale: bool
    :param offset: Offset to apply to the pattern.
    :type offset: float
    :param symlog: To show the data on symlogarithmic scale (z axis) (default False).
    :type symlog: bool
    :param fn_png: The name of the output png file, defaults to `None`.
    :type fn_png: str
    """
    fig, ax = plt.subplots()
    # Get limits.
    mn, mx = pattern.min(), pattern.max()

    x_range, y_range = pattern.shape

    if offset:
        mn = pattern.min() + offset
        mx = pattern.max() + offset
        pattern = pattern.astype(float) + offset

    if (logscale and symlog):
        print('logscale and symlog are both true.\noverrided by logscale')

    # default plot setup
    if (logscale or symlog):
        kwargs['cmap'] = kwargs.pop('cmap', "viridis")
        if logscale:
            kwargs['norm'] = kwargs.pop('norm', colors.LogNorm())
        elif symlog:
            kwargs['norm'] = kwargs.pop('norm', colors.SymLogNorm(0.015))
        axes = kwargs.pop('axes', None)
        plt.imshow(pattern, *argv, **kwargs)
    else:
        kwargs['norm'] = kwargs.pop('norm', colors.Normalize(vmin=mn, vmax=mx))
        kwargs['cmap'] = kwargs.pop('cmap', "viridis")
        plt.imshow(pattern, *argv, **kwargs)

    plt.xlabel(r'$x$ (pixel)')
    plt.ylabel(r'$y$ (pixel)')
    plt.xlim([0, x_range - 1])
    plt.ylim([0, y_range - 1])
    plt.tight_layout()
    plt.colorbar()
    if fn_png:
        plt.savefig(fn_png, dpi=300)
    else:
        plt.show()
