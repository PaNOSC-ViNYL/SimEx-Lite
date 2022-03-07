""":module GaussianSourceCalculator: Module that holds the GaussianSourceCalculator class.  """

from warnings import warn
import sys
import numpy as np
from pathlib import Path
from scipy.constants import hbar, c
from pint import Quantity, Unit
import imp

from libpyvinyl import BaseCalculator, CalculatorParameters
from SimExLite.WavefrontData import WavefrontData, WPGFormat

# WPG is neccessary to execute the calculator, but it's not a hard dependency of SimExLite.
try:
    from wpg.generators import build_gauss_wavefront
    from wpg import Wavefront
    WPG_AVAILABLE = True
except ModuleNotFoundError:
    WPG_AVAILABLE = False


class GaussianSourceCalculator(BaseCalculator):
    """:class GaussianSourceCalculator: Class representing a x-ray free electron laser photon source."""

    def __init__(
        self,
        name: str,
        input=None,
        output_keys: str = "Gaussian_wavefront",
        output_data_types=WavefrontData,
        output_filenames: str = "wavefront.h5",
        instrument_base_dir="./",
        calculator_base_dir="GaussianSourceCalculator",
        parameters=None,
    ):
        if not WPG_AVAILABLE:
            warn('Cannot find the "WPG" module, which is required to run '
                 'GaussianSourceCalculator.backengine(). Is it included in PYTHONPATH?'
                )
        super().__init__(
            name,
            input,
            output_keys,
            output_data_types=output_data_types,
            output_filenames=output_filenames,
            instrument_base_dir=instrument_base_dir,
            calculator_base_dir=calculator_base_dir,
            parameters=parameters,
        )


    def init_parameters(self):
        parameters = CalculatorParameters()

        photon_energy = parameters.new_parameter(
            "photon_energy", comment="The mean photon energy", unit="eV"
        )
        photon_energy.value = 8e3

        relative_bandwidth = parameters.new_parameter(
            "photon_energy_relative_bandwidth", comment="The relative energy bandwidth"
        )
        relative_bandwidth.add_interval(0, None, True)
        relative_bandwidth.value = 1e-3

        diameter = parameters.new_parameter(
            "beam_diameter_fwhm", comment="Beam diameter", unit="m"
        )
        diameter.value = 1e-4

        pulse_energy = parameters.new_parameter(
            "pulse_energy", comment="Total energy of the pulse", unit="joule"
        )
        pulse_energy.value = 2e-3

        divergence = parameters.new_parameter(
            "divergence", comment="Beam divergence angle", unit="radian"
        )
        divergence.add_interval(0, 2 * np.pi, True)
        diver_value = get_divergence_from_beam_diameter(
            photon_energy.value, diameter.value
        )
        divergence.value = diver_value

        spectrum_type = parameters.new_parameter(
            "photon_energy_spectrum_type",
            comment='Type of energy spectrum ("SASE" | "tophat" | "twocolour", default "SASE")',
        )
        spectrum_type.value = "SASE"

        number_of_transverse_grid_points = parameters.new_parameter(
            "number_of_transverse_grid_points",
            comment="The number of grid points in both horizontal (x) and vertical (y) dimension transverse to the beam direction",
        )
        number_of_transverse_grid_points.add_interval(0, None, True)
        number_of_transverse_grid_points.value = 400

        num_time_slices = parameters.new_parameter(
            "number_of_time_slices", comment="The number of time slices"
        )
        num_time_slices.add_interval(0, None, True)
        num_time_slices.value = 12

        param_z = parameters.new_parameter(
            "z", comment="The position of the pulse in the beam direction", unit="m"
        )
        param_z.value = 100

        self.parameters = parameters

    def backengine(self):

        # check for WPG first
        if not WPG_AVAILABLE:
            raise ModuleNotFoundError(
                'Cannot find the "WPG" module, which is required to run '
                'GaussianSourceCalculator.backengine(). Is it included in PYTHONPATH?'
                )

        # The rms of the amplitude distribution (Gaussian)
        theta = self.parameters["divergence"].value_no_conversion.to("radian").magnitude
        E_joule = (
            self.parameters["photon_energy"].value_no_conversion.to("joule").magnitude
        )
        E_eV = self.parameters["photon_energy"].value_no_conversion.to("eV").magnitude
        coherence_time = (
            2.0
            * np.pi
            * hbar
            / self.parameters["photon_energy_relative_bandwidth"].value
            / E_joule
        )
        pulse_energy = self.parameters["pulse_energy"].value_no_conversion

        beam_waist = 2.0 * hbar * c / theta / E_joule
        wavelength = 1239.8e-9 / E_eV
        rayleigh_length = np.pi * beam_waist**2 / wavelength

        print("rayleigh_length =", rayleigh_length)

        beam_diameter_fwhm = (
            self.parameters["beam_diameter_fwhm"]
            .value_no_conversion.to("meter")
            .magnitude
        )
        beam_waist_radius = beam_diameter_fwhm / np.sqrt(2.0 * np.log(2.0))

        # x-y range at beam waist.
        range_xy = 30.0 * beam_waist_radius

        # Set number of sampling points in x and y and number of temporal slices.
        npoints = self.parameters["number_of_transverse_grid_points"].value
        nslices = self.parameters["number_of_time_slices"].value

        # Distance from source position.
        z = self.parameters["z"].value_no_conversion.to("meter").magnitude

        # Build wavefront
        srwl_wf = build_gauss_wavefront(
            npoints,
            npoints,
            nslices,
            E_eV / 1.0e3,
            -range_xy / 2,
            range_xy / 2,
            -range_xy / 2,
            range_xy / 2,
            coherence_time / np.sqrt(2),
            beam_waist_radius / 2,
            beam_waist_radius
            / 2,  # Scaled such that fwhm comes out as demanded by parameters.
            d2waist=z,
            pulseEn=pulse_energy.to("joule").magnitude,
            pulseRange=8.0,
        )

        # Correct radius of curvature.
        Rx = Ry = z * np.sqrt(1.0 + (rayleigh_length / z) ** 2)

        # Store on class.
        srwl_wf.Rx = Rx
        srwl_wf.Ry = Ry

        key = self.output_keys[0]
        filename = self.output_filenames[0]
        output_data = self.output[key]

        wavefront = Wavefront(srwl_wf)
        wavefront.store_hdf5(filename)

        output_data.set_file(filename, WPGFormat)

        return self.output


def get_divergence_from_beam_diameter(E, beam_diameter_fwhm):
    """Calculate the divergence (radian) from and photon energy (eV) beam_diameter (m)"""
    # The rms of the amplitude distribution (Gaussian)
    E = Quantity(E, Unit("eV"))
    beam_waist = beam_diameter_fwhm / np.sqrt(2.0 * np.log(2.0))
    theta = 2.0 * hbar * c / beam_waist / E.to("joule").magnitude

    return float(theta)
