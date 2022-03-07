# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Wavefront Data APIs"""

from libpyvinyl import BaseData


class PMIData(BaseData):
    """PMI structure data mapper"""

    def __init__(
        self,
        key,
        data_dict=None,
        filename=None,
        file_format_class=None,
        file_format_kwargs=None,
    ):

        expected_data = {}

        # A mock of the first time step
        expected_data["0"] = {}
        time_step = expected_data["0"]
        # Number of incident photons
        time_step["num_photons"] = None
        # Atomic numbers of each atom
        time_step["atomic_numbers"] = None
        # Positions in Angstrom of each atom
        time_step["positions"] = None
        # Identification number of each atom
        time_step["id"] = None
        # Charge of each atom. 
        time_step["charge"] = None
        # Unique atom type id per atomic number
        time_step["atom_types"] = None
        time_step["form_factors"] = {}
        form_factors = time_step["form_factors"]
        # Form factors value, shape=(num_atom_types, num_q_range)
        form_factors["value"] = None
        # The scattering vector for the form_factors
        form_factors["q_range"] = None

        # Compton scattering from bound electrons
        time_step["compton_bound"] = {}
        compton_bound = time_step["compton_bound"]
        # Value of compton scattering from bound electrons
        compton_bound["value"] = None
        # The scattering vector for the form_factors
        compton_bound["q_range"] = None

        # Compton scattering from free electrons
        time_step["compton_free"] = {}
        compton_free = time_step["compton_free"]
        # Value of compton scattering from bound electrons
        compton_free["value"] = None
        # The scattering vector for the form_factors
        compton_free["q_range"] = None

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
        return {}

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
