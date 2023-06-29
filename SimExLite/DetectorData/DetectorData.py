# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Detector Data APIs"""

from libpyvinyl import BaseData
from .CXIFormat import CXIFormat


class DetectorData(BaseData):
    """Detector data mapper"""

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
        # Detector raw data
        expected_data["data"] = None
        # Detector mask
        expected_data["mask"] = None
        # Experiment identifier of each frame
        expected_data["experiment_identifier"] = None
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
        self._add_ioformat(format_dict, CXIFormat)
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
