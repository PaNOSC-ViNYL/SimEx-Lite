# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Sample Data APIs"""

from libpyvinyl import BaseData
from .ASEFormat import ASEFormat


class SampleData(BaseData):
    """Sample structure data mapper"""

    def __init__(
        self,
        key,
        data_dict=None,
        filename=None,
        file_format_class=None,
        file_format_kwargs=None,
    ):

        expected_data = {}

        # Atomic position of each atom in angstrom [n, 3] (3D) or [n, 2] (2D)
        expected_data["positions"] = None
        # Atomic number (Z) of each atom
        expected_data["atomic_numbers"] = None
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
        self._add_ioformat(format_dict, ASEFormat)
        return format_dict

    @classmethod
    def from_file(cls, filename: str, format_class, key:str, **kwargs):
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

    def write(self, filename: str, format_class, key: str = None, **kwargs):
        """Write the data mapped by the Data Object into a file and return a Data Object
        mapping the file. It converts either a file or a python object to a file
        The behavior related to a file will always be handled by the format class.
        If it's a python dictionary mapping, write with the specified format_class
        directly.

        :param filename: The filename of the file to be written.
        :type filename: str
        :param file_format_class: The FormatClass to write the file.
        :type file_format_class: class
        :param key: The identification key of the new Data Object. When it's `None`, a new key will
        be generated with a suffix added to the previous identification key by the FormatClass. Defaults to None.
        :type key: str, optional
        :return: A Data Object
        :rtype: BaseData
        """
        if self.mapping_type == dict:
            return format_class.write(self, filename, key, **kwargs)
        elif format_class in self.file_format_class.direct_convert_formats():
            return self.file_format_class.convert(
                self, filename, format_class, key, **kwargs
            )
        else:
            return format_class.write(self, filename, key, **kwargs)
