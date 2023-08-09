""":module XMDYNFormat: Module that holds the XMDYNFormat class."""
import h5py
import numpy as np
from pathlib import Path
from tqdm.autonotebook import tqdm
from ase.io import write
from ase import Atoms

from libpyvinyl.BaseData import BaseData, DataCollection
from libpyvinyl.BaseFormat import BaseFormat
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.utils.Logger import setLogger
from SimExLite.utils.io import parseIndex

my_logger = setLogger(__name__)


class XMDYNFormat(BaseFormat):
    """:class ASEFormat: Class that interfacing data format supported by ASE."""

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def format_register(self):
        key = "XMDYN"
        description = "XMDYN format for PMI data"
        file_extension = [".h5"]
        read_kwargs = [""]
        write_kwargs = [""]
        return self._create_format_register(
            key, description, file_extension, read_kwargs, write_kwargs
        )

    @staticmethod
    def direct_convert_formats():
        # Assume the format can be converted directly to the formats supported by these classes:
        # AFormat, BFormat
        # Redefine this `direct_convert_formats` for a concrete format class
        return [ASEFormat]

    @classmethod
    def read(cls, filename: str, format=None) -> dict:
        """Read the data from the file with the `filename` to a dictionary."""
        # Reference : https://simex.readthedocs.io/en/latest/include/data_formats.html#photon-matter-interaction-xmdyn
        data_dict = {}
        with h5py.File(filename, "r") as h5:
            data = h5["data"]
            for snp in data:
                if snp == "angle":
                    data_dict["angle"] = data[snp][()]
                    continue
                # Input time step
                step_in = data[snp]
                # Output time step
                step = int(snp.strip("snp_")) - 1
                step = str(step)
                data_dict[step] = {}
                time_step = data_dict[step]
                # Time of each step in second
                try:
                    time_step["time"] = h5["misc/time"][snp][()]
                except KeyError:
                    my_logger.warning(
                        f"misc/time not found in the file: {filename}, will set time to 0."
                    )
                    time_step["time"] = 0
                time_step["atomic_numbers"] = step_in["Z"][()]
                # Velocity of each atom. The unit is m/s
                time_step["velocity"] = step_in["Z"][()]
                # Position of each atom. The unit is Angstrom
                time_step["positions"] = step_in["r"][()] * 1e10
                # Charge of each atom.
                try:
                    time_step["charge"] = step_in["charge"]
                except KeyError:
                    my_logger.warning(
                        f"charge not found in the file: {filename}, will set charge to 0."
                    )
                    time_step["charge"] = 0
                # Identification number of each atom
                time_step["id"] = np.arange(len(time_step["atomic_numbers"]))
                # Number of unique atom types
                time_step["num_atom_types"] = len(step_in["T"])
                # Atom type ID of each atom
                time_step["atom_types"] = step_in["xyz"][()]
                # Number of photons
                time_step["num_photons"] = step_in["Nph"][()]
                # Form factors for each atom_type
                time_step["form_factors"] = {}
                form_factors = time_step["form_factors"]
                # Form factors value, shape=(num_atom_types, num_q_range)
                form_factors["value"] = step_in["ff"][()]
                # Convert to q = 2sin(theta)/lambda
                form_factors["q_range"] = step_in["halfQ"][()] * 2

                # Reference: Slowik et al. Journal of Physics 16, 073042 (2014).
                # Compton scattering from free electrons for each atom_type
                time_step["compton_bound"] = {}
                compton_bound = time_step["compton_bound"]
                # Compton from bound electrons value, shape=(num_q_range)
                compton_bound["value"] = step_in["Sq_bound"][()]
                # Convert to q = 2sin(theta)/lambda
                compton_bound["q_range"] = step_in["Sq_halfQ"][()] * 2
                # Compton scattering from free electrons for each atom_type
                time_step["compton_free"] = {}
                compton_free = time_step["compton_free"]
                # Compton from free electrons value, shape=(num_q_range)
                compton_free["value"] = step_in["Sq_free"][()]
                # Convert to q = 2sin(theta)/lambda
                compton_free["q_range"] = step_in["Sq_halfQ"][()] * 2

        return data_dict

    @classmethod
    def write(cls, object, filename: str, key: str = None, format=None):
        """Save the data with the `filename`."""
        data_dict = object.get_data()
        steps = np.array(data_dict.keys()).astype(int)
        steps.sort()
        with h5py.File(filename, "w") as h5:
            data_grp = h5.create_group("data")
            misc_grp = h5.create_group("misc")
            misc_time = misc_grp.create_group("time")
            try:
                angle = data_dict["angle"]
                data_grp["angle"] = angle
            except KeyError:
                pass
            for step in steps:
                snp = f"snp_{step:07}"
                snp_grp = data_grp.create_group(snp)
                time_step = data_dict[str(step)]
                snp_grp["Nph"] = time_step["num_photons"]
                snp_grp["Z"] = time_step["atomic_numbers"]
                snp_grp["r"] = time_step["positions"] * 1e-10  # meter
                snp_grp["T"] = np.arange(time_step["num_atom_types"])
                snp_grp["v"] = time_step["velocity"]
                snp_grp["xyz"] = time_step["atom_types"]
                snp_grp["charge"] = time_step["charge"]
                snp_grp["Sq_bound"] = time_step["compton_bound"]["value"]
                snp_grp["Sq_free"] = time_step["compton_free"]["value"]
                assert (
                    time_step["compton_bound"]["q_range"]
                    == time_step["compton_free"]["q_range"]
                )
                snp_grp["Sq_halfQ"] = time_step["compton_bound"]["q_range"] / 2
                snp_grp["ff"] = time_step["form_factors"]["value"]
                snp_grp["halfQ"] = time_step["form_factors"]["q_range"] / 2
                misc_time[snp] = time_step["time"]

        if key is None:
            original_key = object.key
            key = original_key + "_to_XMDYNormat"
        return object.from_file(filename, cls, key)

    @classmethod
    def convert(
        cls, obj: BaseData, output: str, output_format_class: str, key, **kwargs
    ):
        """Direct convert method, if the default converting would be too slow or not suitable for the output_format"""
        # If there is no direct converting supported:
        if output_format_class is ASEFormat:
            # If there is multiple indices defined, the output class is the last atom file.
            if key is None:
                original_key = obj.key
                key = original_key + "_from_XMDYNFormat_to_ASEFormat"
            return cls.convert_to_ASEFormat(obj.filename, output, key, **kwargs)
        else:
            raise TypeError(
                "Direct converting to format {} is not supported".format(
                    output_format_class
                )
            )
        # Set the key of the returned object
        if key is None:
            original_key = obj.key
            key = original_key + "_from_XMDYNFormat"
        return obj.from_file(output, output_format_class, key)

    @classmethod
    def convert_to_ASEFormat(
        cls, filename: str, output: str, key: str, index: str = ":", format=None
    ):
        """index starts from 0."""
        index = parseIndex(index)
        data_collection = DataCollection()
        with h5py.File(filename, "r") as h5:
            data = h5["data"]
            # frames in XMDYN data
            snps = list(filter(lambda x: x.startswith("snp"), h5["data"]))
            snps.sort()
            snps_to_write = snps[index]
            for snp in tqdm(snps_to_write):
                step_in = data[snp]
                positions = step_in["r"][()] * 1e10 # Angstrom
                atomic_numbers = step_in["Z"][()]
                p_output = Path(output)
                p_stem = p_output.stem + f"_{snp}"
                p_suffix = p_output.suffix
                p_output = p_output.with_name(p_stem + p_suffix)
                atoms = Atoms(atomic_numbers, positions)
                my_logger.info(f"Writing to {p_output} ...")
                write(str(p_output), atoms, format=format)
                key_snp = key + f"_{snp}"
                data_collection.add_data(
                    SampleData.from_file(str(p_output), ASEFormat, key_snp)
                )
        # Return the last filename.
        return data_collection
