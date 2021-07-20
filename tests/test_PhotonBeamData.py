"""Test PhotonBeamData"""

import pytest
import numpy as np
from SimExLite.PhotonBeamData import SimpleBeam


def test_wavelength_construct():
    SB = SimpleBeam(wavelength=1.54, pulse_energy=1.04e-3)
    print(SB.attrs)
    SB.showAttrs()
    assert pytest.approx(SB.get_photon_energy().to('keV').magnitude,
                         0.01) == 8.05


def test_wavelength_array_construct():
    lambda_arr = np.array([1.53, 1.54, 1.55])
    lambda_weights = np.array([0.2, 0.7, 0.1])
    SB = SimpleBeam(wavelength=lambda_arr,
                    wavelength_weights=lambda_weights,
                    pulse_energy=1.04e-3)
    print(SB.attrs)
    SB.showAttrs()
    assert pytest.approx(SB.get_photon_energy().to('keV').magnitude,
                         0.01) == 8.05


def test_beam_size_construct():
    lambda_arr = np.array([1.53, 1.54, 1.55])
    lambda_weights = np.array([0.2, 0.7, 0.1])
    beam_size = [400, 400]
    SB = SimpleBeam(wavelength=lambda_arr,
                    wavelength_weights=lambda_weights,
                    pulse_energy=1.04e-3)
    SB.set_beam_size(beam_size, 'um')
    print(SB.attrs)
    SB.showAttrs()
    print(SB.get_focus_area('um**2'))
    assert pytest.approx(SB.get_photon_energy().to('keV').magnitude,
                         0.01) == 8.05


def test_beam_size_rect():
    lambda_arr = np.array([1.53, 1.54, 1.55])
    lambda_weights = np.array([0.2, 0.7, 0.1])
    beam_size = [400, 400]
    SB = SimpleBeam(wavelength=lambda_arr,
                    wavelength_weights=lambda_weights,
                    pulse_energy=1.04e-3,
                    profile='rectangular')
    SB.set_beam_size(beam_size, 'um')
    print(SB.attrs)
    SB.showAttrs()
    print('focus_area = {:.3~P}'.format(SB.get_focus_area('um**2')))
    assert pytest.approx(SB.get_photon_energy().to('keV').magnitude,
                         0.01) == 8.05
    assert pytest.approx(SB.get_focus_area().to('um**2').magnitude,
                         0.01) == 1.6e5


def test_photon_energy_construct():
    SB = SimpleBeam(photon_energy=8.05e3, pulse_energy=1.04e-3)
    SB.set_focus_area(15 * 15, unit='um**2')
    assert pytest.approx(SB.get_wavelength().to('angstrom').to_tuple()[0],
                         0.01) == 1.54
    assert pytest.approx(SB.get_photons_per_pulse().to_tuple()[0],
                         0.01) == 8.1e11
    assert pytest.approx(SB.get_fluence().to('J/cm**2').to_tuple()[0],
                         0.01) == 4.6e2


if __name__ == "__main__":
    test_wavelength_array_construct()
    test_beam_size_construct()
    test_beam_size_rect()