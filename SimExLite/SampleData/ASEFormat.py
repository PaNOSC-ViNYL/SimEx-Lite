""":module ASEFormat: Module that holds the ASEFormat class."""
from libpyvinyl.BaseFormat import BaseFormat
from .SampleData import SampleData
from ase.io import read, write
from ase import Atoms


class ASEFormat(BaseFormat):
    """:class ASEFormat: Class that interfacing data format supported by ASE."""

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def format_register(self):
        key = "ASE"
        description = "ASE wrapper for sample data"
        file_extension = ["Any"]
        read_kwargs = ["format"]
        write_kwargs = ["format"]
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
    def read(cls, filename: str, format=None) -> dict:
        """Read the data from the file with the `filename` to a dictionary."""
        # Reference : https://wiki.fysik.dtu.dk/ase/ase/io/io.html
        atoms = read(filename, format=format)
        data_dict = {}
        data_dict["positions"] = atoms.positions
        data_dict["atomic_numbers"] = atoms.numbers

        return data_dict

    @classmethod
    def write(cls, object: SampleData, filename: str, key: str = None, format=None):
        """Save the data with the `filename`."""
        data_dict = object.get_data()
        atoms = Atoms(data_dict["atomic_numbers"], data_dict["positions"])
        write(filename, atoms, format=format)

        if key is None:
            original_key = object.key
            key = original_key + "_to_ASEFormat"
        return object.from_file(filename, cls, key)
