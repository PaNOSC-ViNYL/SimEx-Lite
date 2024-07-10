# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

from tqdm.autonotebook import tqdm
from pathlib import Path
import h5py
import numpy as np
from libpyvinyl import BaseData
from SimExLite.utils.analysis import linear
from SimExLite.utils import rebin_sum
from .SingFELFormat import SingFELFormat
from .EMCFormat import EMCFormat
from .CustomizedFormat import CustomizedFormat
from . import writeemc


def spliterate(buf, chunk):
    for start in range(0, len(buf), chunk):
        # print(start, start+chunk)
        yield buf[start : start + chunk]


class DiffractionData(BaseData):
    """Diffraction data mapper"""

    def __init__(
        self,
        key,
        data_dict=None,
        filename=None,
        file_format_class=None,
        file_format_kwargs=None,
    ):
        expected_data = {}

        ### DataClass developer's job start
        # The image array of the diffraction patterns shape=(nframe, py, px)
        expected_data["img_array"] = None
        # Sample to detector distance
        expected_data["distance"] = None
        # Quaternions of each diffraction pattern
        expected_data["quaternions"] = None
        # Quaternions of each diffraction pattern
        expected_data["geom"] = None
        ### DataClass developer's job end

        super().__init__(
            key,
            expected_data,
            data_dict,
            filename,
            file_format_class,
            file_format_kwargs,
        )

    @classmethod
    def supported_formats(self):
        format_dict = {}
        self._add_ioformat(format_dict, SingFELFormat)
        self._add_ioformat(format_dict, EMCFormat)
        self._add_ioformat(format_dict, CustomizedFormat)
        return format_dict

    @classmethod
    def from_file(cls, filename: str, format_class, key: str, **kwargs):
        return cls(
            key,
            filename=filename,
            file_format_class=format_class,
            file_format_kwargs=kwargs,
        )

    @classmethod
    def from_dict(cls, data_dict, key):
        """Create the data class by a python dictionary."""
        return cls(key, data_dict=data_dict)

    def multiply(self, val, chunk_size=10000):
        """Multiply a number to the diffraction patterns.

        Args:
            val (float): The value to be multiplied.
            chunk (int): The chunk size to conduct the operation
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        if isinstance(val, np.ndarray):
            array[:] = array * val
        else:
            n_chunks = int(np.ceil(float(len(array)) / chunk_size))
            print(f"Operation in {n_chunks} chunks", flush=True)
            for arr in tqdm(
                spliterate(array, chunk_size),
                total=n_chunks,
            ):
                arr[:] = arr * val

    def add_beam_stop(self, stop_rad: float):
        """Add a beamstop in pixel radius (float) to the diffraction patterns.

        Args:
            stop_rad (float): The radius of the beamstop in pixel unit
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        print("Adding beam stop...", flush=True)
        for i, img in enumerate(tqdm(array)):
            array[i] = addBeamStop(img, stop_rad)
        self.stop_rad = stop_rad

    def add_Gaussian_noise(self, mu, sigs_popt):
        """Add Gaussian noise to one diffraction pattern

        Args:
            mu (float): The averange ADU for one photon
            sigs_popt (list): [slop, intercept]
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        print("Adding Gaussian Noise...", flush=True)
        for i, diffr_data in enumerate(tqdm(array)):
            array[i] = addGaussianNoise(diffr_data, mu, sigs_popt)

    def poissonize(self):
        """Poissonize the data array in this data class"""
        self.__operation_check()
        array = self.data_dict["img_array"]
        array[:] = np.random.poisson(array)

    def set_array_data_type(self, data_type):
        """The the data numpy array dtype

        Args:
            data_type (numpy.dtype): The numpy dtype to be set. E.g. 'int32'
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        self.data_dict["img_array"] = array.astype(data_type)

    def apply_geom_mask(self, geom):
        """Apply the mask from a detector geom to the data, detector gaps will be filled with -1.

        Args:
            geom (ExtraGeomDetectorGeometry): extra_geom instance
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        mask = get_geom_mask(geom, self.data_dict["img_array"][0].shape)
        print("Applying the mask...", flush=True)
        for diffr_data in tqdm(array):
            diffr_data[np.isnan(mask)] = -1
        return mask

    def __operation_check(self):
        """To check if the data operation is allowed."""
        if self.data_dict is None:
            err_str = (
                "This operation is only avaiable for dict type data. To convert:\n"
            )
            err_str += "my_dict = YOUR_INSTANCE.get_data() \n"
            err_str += "dd_in_dict = DiffractionData.from_dict(my_dict, 'YOUR_KEY')"

            raise TypeError(err_str)


def addBeamStop(img, stop_rad):
    """Add the beamstop in pixel radius to diffraction pattern.

    Args:
        img (ndarray): Diffraction pattern
        stop_rad (float): The radius of the beamstop in pixel unit (float)

    Returns:
        ndarray: Beamstop masked 2D array
    """
    stop_mask = np.ones_like(img)
    center = np.array(img.shape) // 2
    y = np.indices(img.shape)[0] - center[0]
    x = np.indices(img.shape)[1] - center[1]
    r = np.sqrt((x * x + y * y))
    stop_mask[r <= stop_rad] = 0
    masked = img * stop_mask
    return masked


def write_multiple_file_to_emc(
    in_file_list,
    in_file_format_class,
    filename: str,
    poissonize=False,
    stop_rad=None,
    multiply=None,
    fluct_sample_interval=None,
    background=None,
    geom=None,
    **kwargs,
):
    """Write multiple diffraction files to a single EMC h5 file"""
    # Normally fluct_sample_interval is set to 3.
    emcwriter = None
    list_len = len(in_file_list)
    if fluct_sample_interval is not None:
        fluct_I = []
    for idx, in_fn in enumerate(in_file_list):
        print(f"{idx + 1}/{list_len}: {in_fn}\n")
        data_dict = in_file_format_class.read(in_fn, **kwargs)
        dd_in_dict = DiffractionData.from_dict(data_dict, "tmp")
        # Scaling before Poissionization
        arr = data_dict["img_array"]
        if fluct_sample_interval is not None:
            I, _ = get_I(len(arr), fluct_sample_interval)
            arr[:] = arr * I[:, None, None]
            fluct_I.append(I)
        if multiply is not None:
            dd_in_dict.multiply(multiply)
        if background is not None:
            arr[:] += background
        if poissonize:
            dd_in_dict.poissonize()
        if stop_rad is not None:
            dd_in_dict.add_beam_stop(stop_rad)
        if geom is not None:
            dd_in_dict.apply_geom_mask(geom)

        if emcwriter is None:
            arr_sample = arr[0]
            emcwriter = writeemc.EMCWriter(
                filename, arr_sample.shape[0] * arr_sample.shape[1]
            )
        for photons in tqdm(arr):
            emcwriter.write_frame(photons.astype(np.int32).ravel())
    if fluct_sample_interval is not None:
        # fluct_fn = str(Path(filename).with_suffix(".fluct.h5"))
        # with h5py.File(fluct_fn, "w") as h5:
        with h5py.File(filename, "a") as h5:
            h5["fluct_I"] = np.array(fluct_I).ravel()


def get_I(n_patterns, sampling_interval):
    rng = np.random.default_rng()
    R = sampling_interval * np.sqrt(
        rng.random(
            n_patterns,
        )
    )  # independently samples the radius uniformly inside a circle N times
    I = np.exp(-(R**2) / 2)
    return I, R


def addGaussianNoise(diffr_data, mu, sigs_popt):
    """Add Gaussian noise to one diffraction pattern

    Args:
        diffr_data (ndarray): A diffraction pattern.
        mu (float): The average ADU for one photon.
        sigs_popt (list): [slop, intercept].
    """
    sig_arr = linear(diffr_data, *sigs_popt)
    diffr_noise = np.random.normal(diffr_data * mu, sig_arr)
    return diffr_noise


def get_geom_mask(geom, img_size):
    """Get a 2D mask from a detector geom

    Args:
        geom (ExtraGeomDetectorGeometry): extra_geom instance.
        img_size ([nrow, ncol]): The array size of the output mask.
    """
    data = np.ones(geom.expected_data_shape)
    mask, centre = geom.position_modules(data)
    # Get the mask looking from beam upstream
    mask = mask[::-1][::-1]
    new_mask = rebin_sum(mask, img_size)
    new_mask[~np.isnan(new_mask)] = 1
    return new_mask


def get_radial_map(arr):
    """Get the radial map of a 2D array"""
    pmap = np.indices(arr.shape)
    center = np.array(arr.shape) / 2.0
    center = center[:, np.newaxis, np.newaxis]
    r_map = pmap - center
    pixel_map = np.linalg.norm(r_map, axis=0)
    return pixel_map


def get_q(Rs, distance, wavelength):
    """Rs is a collection of the radial distance of pixels.
    distance is the sample to detector distance in pixel unit (distance = real_distance/pixel_size).
    """

    # Convert it to numpy array
    Rs = np.array(Rs)
    twotheta = np.arctan2(Rs, distance)
    q = (2 * np.sin(twotheta / 2.0)) / wavelength
    return q


def R_d(pix_range, img, img_ref, sa_array):
    """
    Get R factor for a certain q range. (See E et. al. 10.1038/s41598-021-97142-5).
    Here it assumes that the solid angles have already been applied to the input image and reference image,
    and the input solid angles are used to get the square root of intensity withtout solid angles.

    Args:
        pix_range (ndarray): A 1D array specifying the indices of pixels of the image for R factor calculation.
        img (ndarray): A 2D array of the image for R factor analysis.
        img_ref (ndarray): A 2D array of the reference image for R factor analysis.
        sa_array (ndarray): The solid angle of each pixel for the diffraction image.

    Returns:
        ndarray: The R factor for this certain pixel range.
    """

    # Make sure it's a 1D array.
    pix_range = np.ravel(pix_range)
    img = np.moveaxis(img, 0, 2)
    img = img.reshape(len(pix_range), -1)
    img_ref = np.moveaxis(img_ref, 0, 2)
    img_ref = img_ref.reshape(len(pix_range), -1)
    sa_array = np.ravel(sa_array)
    sa_sub = sa_array[pix_range]
    sa_sub = sa_sub[:, np.newaxis]

    N_real_sub = img[pix_range] / sa_sub
    N_ideal_sub = img_ref[pix_range] / sa_sub

    N_d = np.sum(np.sqrt(N_real_sub) * sa_sub, axis=0)
    N_ideal_d = np.sum(np.sqrt(N_ideal_sub) * sa_sub, axis=0)

    eqs = abs(np.sqrt(N_real_sub) / N_d - np.sqrt(N_ideal_sub) / N_ideal_d) * sa_sub

    return np.sum(eqs, axis=0)


def get_rfactor(
    img, img_ref, sa_array, pixel_map=None, bin_range=None, bin_size: float = 1.0
):
    """Get the residual factor between two reciprocal space volumes.

    Args:
        img (ndarray): A 3D array (num_snapshot, ny, nx).
        img_ref (ndarray): A 3D reference array (num_snapshot, ny, nx).
        sa_array (ndarray): A 2D array of the solid angle of each pixel for the detector.
        pixel_map (ndarray): A 2D array defines the map the pixels, defaults to the array's indices.
        bin_range (float): The range of bins in the unit of the pixel map, defaults to cover the whole 2D pattern.
        bin_size (float): The pixel interval between two bins, defaults to 1.0.

    Returns:
        (bins, R_factors): A tuple of the r factors and their corresponding radial pixel indices.
    """
    if len(img.shape) != 3 or len(img_ref.shape) != 3:
        raise ValueError(
            "The shape of the input array has to be (num_snapshot, ny, nx)"
        )
    if pixel_map is None:
        pmap = np.indices(img[0].shape)
        center = np.array(img[0].shape) / 2.0
        center = center[:, np.newaxis, np.newaxis]
        # Radial map
        r_map = pmap - center
        pixel_map = np.linalg.norm(r_map, axis=0)
    else:
        pass

    if bin_range is None:
        bin_range = [pixel_map.min(), pixel_map.max()]
    else:
        pass

    bins = np.arange(bin_range[0], bin_range[1] + bin_size, bin_size)
    R_factors = []
    for i in tqdm(bins):
        pixel_range = np.ravel(pixel_map <= i)
        R_factors.append(R_d(pixel_range, img, img_ref, sa_array))
    return bins, np.array(R_factors)
