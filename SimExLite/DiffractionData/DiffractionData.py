# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Diffraction Data APIs"""

from tqdm import tqdm
from pathlib import Path
import h5py
import numpy as np
from libpyvinyl import BaseData
from .SingFELFormat import SingFELFormat
from .EMCFormat import EMCFormat
from .CondorFormat import CondorFormat
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
        self._add_ioformat(format_dict, CondorFormat)
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
        :param val: The value to be multiplied.
        :type val: float
        :param chunk: The chunk size to conduct the operation
        :type chunk_size: int
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

    def addBeamStop(self, stop_rad: float):
        """Add a beamstop in pixel radius (float) to the diffraction patterns.
        :param stop_rad: The radius of the beamstop in pixel unit
        :type stop_rad: float
        """
        self.__operation_check()
        array = self.data_dict["img_array"]
        print("Adding beam stop...", flush=True)
        for i, img in enumerate(tqdm(array)):
            array[i] = addBeamStop(img, stop_rad)
        self.stop_rad = stop_rad

    def poissonize(self):
        """Poissonize the data array in this data class"""
        self.__operation_check()
        array = self.data_dict["img_array"]
        array[:] = np.random.poisson(array)

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
    :param img: Diffraction pattern
    :type img: np.2darray
    :param stop_rad: The radius of the beamstop in pixel unit (float)
    :type stop_rad: float
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


def write_multiple_file_to_emc(
    in_file_list,
    in_file_format_class,
    filename: str,
    poissonize=False,
    stop_rad=None,
    multiply=None,
    fluct_sample_interval=None,
    background=None,
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
        if poissonize:
            dd_in_dict.poissonize()
        if background is not None:
            arr[:] += background
        if stop_rad is not None:
            dd_in_dict.addBeamStop(stop_rad)

        if emcwriter is None:
            arr_sample = arr[0]
            emcwriter = writeemc.EMCWriter(
                filename, arr_sample.shape[0] * arr_sample.shape[1]
            )
        for photons in tqdm(arr):
            emcwriter.write_frame(photons.astype(np.int32).ravel())
    if fluct_sample_interval is not None:
        fluct_fn = str(Path(filename).with_suffix(".fluct.h5"))
        with h5py.File(fluct_fn, "w") as h5:
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
