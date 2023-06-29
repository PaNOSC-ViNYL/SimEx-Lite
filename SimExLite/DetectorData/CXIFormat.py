import h5py
import numpy as np
from numpy import ndarray
from libpyvinyl.BaseFormat import BaseFormat
from SimExLite.utils.io import parseIndex
from SimExLite.utils.Logger import setLogger

logger = setLogger(__name__)


class CXIFormat(BaseFormat):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def format_register(self):
        key = "CXI"
        description = "CXI format for DiffractionData"
        file_extension = ".cxi"
        read_kwargs = ["index"]
        write_kwargs = ["index"]
        return self._create_format_register(
            key, description, file_extension, read_kwargs, write_kwargs
        )

    @staticmethod
    def direct_convert_formats():
        # Assume the format can be converted directly to the formats supported by these classes:
        # AFormat, BFormat
        # Redefine this `direct_convert_formats` for a concrete format class
        return []

    @classmethod
    def read(cls, filename: str, index=None) -> dict:
        """Read the data from the file with the `filename` to a dictionary."""
        data_dict = {}

        index = parseIndex(index)
        with h5py.File(filename, "r") as h5:
            n_frame = len(range(len(h5["/entry_1/data_1/data"]))[index])
            logger.info(f"Reading {n_frame} frames")
            logger.info("Reading data...")
            data_dict["data"] = h5["/entry_1/data_1/data"][index]
            logger.info("Reading mask...")
            data_dict["mask"] = h5["/entry_1/data_1/mask"][index]
            logger.info("Reading experiment_identifier...")
            data_dict["experiment_identifier"] = h5["/entry_1/experiment_identifier"][
                index
            ]
            logger.info("Reading done...")

        return data_dict

    @classmethod
    def write(cls, object, filename: str, key: str = None):
        """Save the data with the `filename`."""
        data_dict = object.get_data()
        with h5py.File(filename, "w") as h5:
            entry_1 = h5.create_group("/entry_1")
            instrument_1 = entry_1.create_group("instrument_1")
            detector_1 = instrument_1.create_group("detector_1")
            detector_1.create_dataset("data", data=data_dict["data"])
            detector_1.create_dataset("mask", data=data_dict["mask"])
            entry_1.create_dataset(
                "experiment_identifier", data=data_dict["experiment_identifier"]
            )
            detector_1["experiment_identifier"] = h5py.SoftLink(
                entry_1["experiment_identifier"].name
            )
            h5["/entry_1/data_1"] = h5py.SoftLink(detector_1.name)

        if key is None:
            original_key = object.key
            key = original_key + "_to_CXIFormat"
        return object.from_file(filename, cls, key)
